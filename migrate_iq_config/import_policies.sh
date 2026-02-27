#!/bin/bash
source ./config.sh

EXPORT_FILE="${EXPORT_FILE_POLICIES:-./migration_data/policies_bundle.json}"
GLOBAL_TAG_MAP="./migration_data/global_tag_map.txt"

# Convert Tag Map to JSON for JQ lookup
TAG_MAP_JSON=$(jq -Rs 'split("\n") | map(select(length > 0) | split("|")) | map({(.[0]): .[1]}) | add' "$GLOBAL_TAG_MAP")

echo "--- STARTING POLICY IMPORT ---"

jq -c '.[]' "$EXPORT_FILE" | while read -r bundle; do
    ORG_NAME=$(echo "$bundle" | jq -r '.orgName')
    
    # Resolve Target Org ID
    TARGET_ORG_ID=$(curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/organizations" | jq -r --arg n "$ORG_NAME" '.organizations[] | select(.name==$n) | .id' | head -n 1)

    echo "Importing policies to: $ORG_NAME"

    echo "$bundle" | jq -c '.policies[]?' 2>/dev/null | while read -r policy; do
        P_NAME=$(echo "$policy" | jq -r '.name')
        
        # REMAP Category IDs within the policy conditions
        # This part looks for any condition using a tag and replaces the old ID with the new one
        REMAPPED_POLICY=$(echo "$policy" | jq --argjson tagMap "$TAG_MAP_JSON" '
            walk(
                if type == "object" and .conditionType == "APPLICATION_CATEGORY" then
                    .value = ($tagMap[.value] // .value)
                else . end
            ) | del(.id, .organizationId)
        ')

        echo "  - Creating Policy: $P_NAME"
        curl -u "$TARGET_USER" -s -X POST -H "Content-Type: application/json" \
            -d "$REMAPPED_POLICY" \
            "$TARGET_URL/api/v2/policies/organization/$TARGET_ORG_ID" > /dev/null
    done
done

echo "--- POLICY MIGRATION FINISHED ---"
