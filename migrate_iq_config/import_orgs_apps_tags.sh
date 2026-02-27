#!/bin/bash
source ./config.sh

EXPORT_FILE="${EXPORT_FILE:-./migration_data/full_migration_bundle.json}"
GLOBAL_TAG_MAP="./migration_data/global_tag_map.txt"

echo "--- STARTING FULL IMPORT ---"

fetch_target_orgs() {
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/organizations"
}

echo "--- PREPARING GLOBAL TAG MAP ---"
> "$GLOBAL_TAG_MAP"
ORGS_RAW=$(fetch_target_orgs)

echo "$ORGS_RAW" | jq -c '.organizations[]?' | while read -r org; do
    OID=$(echo "$org" | jq -r '.id')
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applicationCategories/organization/$OID" | \
    jq -r 'if type == "array" then .[] else .categories[]? end | "\(.name)|\(.id)"' 2>/dev/null >> "$GLOBAL_TAG_MAP"
done

MAP_JSON=$(jq -Rs 'split("\n") | map(select(length > 0) | split("|")) | map({(.[0]): .[1]}) | add' "$GLOBAL_TAG_MAP")
[ "$MAP_JSON" == "null" ] && MAP_JSON="{}"

echo "--- STEP 2: UPSERTING APPLICATIONS & LINKING TAGS ---"

jq -c '.[]' "$EXPORT_FILE" | while read -r bundle; do
    ORG_NAME=$(echo "$bundle" | jq -r '.organization.name')
    TARGET_ORG_ID=$(echo "$ORGS_RAW" | jq -r --arg n "$ORG_NAME" '.organizations[]? | select(.name==$n) | .id' | head -n 1)

    if [[ -z "$TARGET_ORG_ID" || "$TARGET_ORG_ID" == "null" ]]; then
        echo "  Creating Org: $ORG_NAME"
        CREATE_RES=$(curl -u "$TARGET_USER" -s -X POST -H "Content-Type: application/json" -d "{\"name\":\"$ORG_NAME\"}" "$TARGET_URL/api/v2/organizations")
        TARGET_ORG_ID=$(echo "$CREATE_RES" | jq -r '.id // empty' | head -n 1)
        ORGS_RAW=$(fetch_target_orgs)
    fi

    echo "Processing Org: $ORG_NAME"

    echo "$bundle" | jq -c '.applications[]?' | while read -r app; do
        APP_NAME=$(echo "$app" | jq -r '.name' | xargs)
        APP_PID=$(echo "$app" | jq -r '.publicId' | xargs)
        
        MAPPED_TAGS=$(echo "$app" | jq --argjson map "$MAP_JSON" '
            [ .applicationTags[]? | select(.tagName != null and .tagName != "Unknown") | {tagId: $map[.tagName]} | select(.tagId != null) ]
        ' 2>/dev/null)
        [[ -z "$MAPPED_TAGS" ]] && MAPPED_TAGS="[]"

        PAYLOAD=$(jq -n --arg pid "$APP_PID" --arg name "$APP_NAME" --arg oid "$TARGET_ORG_ID" --argjson tags "$MAPPED_TAGS" \
            '{publicId: $pid, name: $name, organizationId: $oid, applicationTags: $tags}')

        # 1. Check if app already exists on target
        EXISTING_APP_STATUS=$(curl -u "$TARGET_USER" -s -o /dev/null -w "%{http_code}" "$TARGET_URL/api/v2/applications?publicId=$APP_PID")

        if [[ "$EXISTING_APP_STATUS" == "200" ]]; then
            # 2. APP EXISTS: Update it
            # We fetch the internal ID first for the PUT URL
            INTERNAL_ID=$(curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applications?publicId=$APP_PID" | jq -r '.applications[0].id')
            echo -n "    - $APP_NAME: Updating tags... "
            curl -u "$TARGET_USER" -s -X PUT -H "Content-Type: application/json" -d "$PAYLOAD" "$TARGET_URL/api/v2/applications/$INTERNAL_ID" > /dev/null
            echo "Done."
        else
            # 3. APP MISSING: Create it
            echo -n "    - $APP_NAME: Creating... "
            CREATE_RESPONSE=$(curl -u "$TARGET_USER" -s -i -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$TARGET_URL/api/v2/applications")
            CREATE_STATUS=$(echo "$CREATE_RESPONSE" | grep HTTP | tail -1 | awk '{print $2}')
            
            if [[ "$CREATE_STATUS" == "201" || "$CREATE_STATUS" == "200" ]]; then
                echo "Success."
            else
                echo "FAILED ($CREATE_STATUS)"
                echo "      REASON: $(echo "$CREATE_RESPONSE" | sed '1,/^\r$/d')"
            fi
        fi
    done
done
echo "--- MIGRATION COMPLETE ---"
