#!/bin/bash
source ./config.sh

EXPORT_FILE="${EXPORT_FILE:-./migration_data/full_migration_bundle.json}"
GLOBAL_TAG_MAP="./migration_data/global_tag_map.txt"

# Step 1: Re-build the map from what is currently on the Target
# This ensures we have the latest IDs even if the script was interrupted
echo "--- PREPARING GLOBAL TAG MAP ---"
> "$GLOBAL_TAG_MAP"
ORGS_RAW=$(curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/organizations")
echo "$ORGS_RAW" | jq -c '.organizations[]?' | while read -r org; do
    OID=$(echo "$org" | jq -r '.id')
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applicationCategories/organization/$OID" | \
    jq -r 'if type == "array" then .[] else .categories[]? end | "\(.name)|\(.id)"' 2>/dev/null >> "$GLOBAL_TAG_MAP"
done
sort -u "$GLOBAL_TAG_MAP" -o "$GLOBAL_TAG_MAP"

# Convert map to JSON for JQ speed
MAP_JSON=$(jq -Rs 'split("\n") | map(select(length > 0) | split("|")) | map({(.[0]): .[1]}) | add' "$GLOBAL_TAG_MAP")

echo "--- STEP 2: CREATING APPLICATIONS & LINKING TAGS ---"

jq -c '.[]' "$EXPORT_FILE" | while read -r bundle; do
    ORG_NAME=$(echo "$bundle" | jq -r '.organization.name')
    
    # Get the Target Org ID
    TARGET_ORG_ID=$(echo "$ORGS_RAW" | jq -r --arg n "$ORG_NAME" '.organizations[] | select(.name==$n) | .id' | head -n 1)

    if [[ -z "$TARGET_ORG_ID" || "$TARGET_ORG_ID" == "null" ]]; then
        echo "  [SKIP] Org $ORG_NAME not found. Run Step 1 of the previous script to create Orgs."
        continue
    fi

    echo "Processing Apps for: $ORG_NAME"

    echo "$bundle" | jq -c '.applications[]?' 2>/dev/null | while read -r app; do
        APP_NAME=$(echo "$app" | jq -r '.name')
        APP_PID=$(echo "$app" | jq -r '.publicId')
        
        # Build the Tag ID list from our Map
        MAPPED_TAGS=$(echo "$app" | jq --argjson map "$MAP_JSON" '
            [ .applicationTags[]? | select(.tagName != null and .tagName != "Unknown") | {tagId: $map[.tagName]} | select(.tagId != null) ]
        ' 2>/dev/null)

        # Build the full Application Payload
        # Note: We must include organizationId for the POST to work
        PAYLOAD=$(echo "$app" | jq --argjson tags "$MAPPED_TAGS" --arg oid "$TARGET_ORG_ID" \
            '{publicId: .publicId, name: .name, organizationId: $oid, applicationTags: $tags}')

        # Try to CREATE the app (POST)
        echo -n "  - $APP_NAME: "
        RESPONSE_CODE=$(curl -u "$TARGET_USER" -s -o /dev/null -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" -d "$PAYLOAD" \
            "$TARGET_URL/api/v2/applications")

        if [[ "$RESPONSE_CODE" == "201" || "$RESPONSE_CODE" == "200" ]]; then
            echo "Created successfully with $(echo "$MAPPED_TAGS" | jq 'length') tags."
        elif [[ "$RESPONSE_CODE" == "409" ]]; then
            # App already exists, so UPDATE it (PUT)
            curl -u "$TARGET_USER" -s -X PUT -H "Content-Type: application/json" \
                -d "$PAYLOAD" "$TARGET_URL/api/v2/applications/$APP_PID" > /dev/null
            echo "Already exists. Updated tags."
        else
            echo "FAILED (HTTP $RESPONSE_CODE)"
        fi
    done
done

echo "--- MIGRATION COMPLETE ---"

