#!/bin/bash
source ./config.sh

EXPORT_FILE="${EXPORT_FILE:-./migration_data/full_migration_bundle.json}"
GLOBAL_TAG_MAP="./migration_data/global_tag_map.txt"

echo "--- STARTING FULL IMPORT ---"

# 1. RE-FETCH ALL ORGS FROM TARGET
fetch_target_orgs() {
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/organizations"
}

# 2. PREPARE TAG MAP (FETCH CURRENT STATE)
echo "--- PREPARING GLOBAL TAG MAP ---"
> "$GLOBAL_TAG_MAP"
ORGS_RAW=$(fetch_target_orgs)

echo "$ORGS_RAW" | jq -c '.organizations[]?' | while read -r org; do
    OID=$(echo "$org" | jq -r '.id')
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applicationCategories/organization/$OID" | \
    jq -r 'if type == "array" then .[] else .categories[]? end | "\(.name)|\(.id)"' 2>/dev/null >> "$GLOBAL_TAG_MAP"
done
sort -u "$GLOBAL_TAG_MAP" -o "$GLOBAL_TAG_MAP"

# Convert map to JSON
MAP_JSON=$(jq -Rs 'split("\n") | map(select(length > 0) | split("|")) | map({(.[0]): .[1]}) | add' "$GLOBAL_TAG_MAP")

echo "--- STEP 2: CREATING ORGS, APPS & LINKING TAGS ---"

jq -c '.[]' "$EXPORT_FILE" | while read -r bundle; do
    ORG_NAME=$(echo "$bundle" | jq -r '.organization.name')
    
    # Check if Org exists
    TARGET_ORG_ID=$(echo "$ORGS_RAW" | jq -r --arg n "$ORG_NAME" '.organizations[]? | select(.name==$n) | .id' | head -n 1)

    # AUTO-HEAL: If Org is missing, create it
    if [[ -z "$TARGET_ORG_ID" || "$TARGET_ORG_ID" == "null" ]]; then
        echo "  [NEW] Creating Org: $ORG_NAME"
        CREATE_RES=$(curl -u "$TARGET_USER" -s -X POST -H "Content-Type: application/json" -d "{\"name\":\"$ORG_NAME\"}" "$TARGET_URL/api/v2/organizations")
        TARGET_ORG_ID=$(echo "$CREATE_RES" | jq -r '.id // empty' | head -n 1)
        # Refresh ORGS_RAW so subsequent apps in this run know the Org exists
        ORGS_RAW=$(fetch_target_orgs)
    fi

    echo "Processing Apps for: $ORG_NAME"

    echo "$bundle" | jq -c '.applications[]?' 2>/dev/null | while read -r app; do
        APP_NAME=$(echo "$app" | jq -r '.name')
        APP_PID=$(echo "$app" | jq -r '.publicId')
        
        # Build Tag ID list
        MAPPED_TAGS=$(echo "$app" | jq --argjson map "$MAP_JSON" '
            [ .applicationTags[]? | select(.tagName != null and .tagName != "Unknown") | {tagId: $map[.tagName]} | select(.tagId != null) ]
        ' 2>/dev/null)

        PAYLOAD=$(echo "$app" | jq --argjson tags "$MAPPED_TAGS" --arg oid "$TARGET_ORG_ID" \
            '{publicId: .publicId, name: .name, organizationId: $oid, applicationTags: $tags}')

        # Try POST (Create)
        RESPONSE_CODE=$(curl -u "$TARGET_USER" -s -o /dev/null -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" -d "$PAYLOAD" \
            "$TARGET_URL/api/v2/applications")

        if [[ "$RESPONSE_CODE" == "201" || "$RESPONSE_CODE" == "200" ]]; then
            echo "    - $APP_NAME: Created"
        elif [[ "$RESPONSE_CODE" == "409" ]]; then
            # Already exists, Update tags
            curl -u "$TARGET_USER" -s -X PUT -H "Content-Type: application/json" \
                -d "$PAYLOAD" "$TARGET_URL/api/v2/applications/$APP_PID" > /dev/null
            echo "    - $APP_NAME: Updated Tags"
        else
            echo "    - $APP_NAME: FAILED ($RESPONSE_CODE)"
        fi
    done
done

# Final Verification
echo "--- FINAL VERIFICATION ---"
curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applications" | jq '[.applications[] | {name: .name, tags: (.applicationTags | length)}] | sort_by(.tags) | reverse'

echo "--- MIGRATION COMPLETE ---"