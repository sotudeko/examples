#!/bin/bash
source ./config.sh

EXPORT_FILE="./migration_data/full_migration_bundle.json"
GLOBAL_TAG_MAP="./migration_data/global_tag_map_final.txt"

echo "--- STARTING COLOR-SAFE IMPORT ---"
> "$GLOBAL_TAG_MAP"

get_org_id() {
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/organizations" | \
    jq -r --arg n "$1" '.organizations[]? | select(.name==$n) | .id' | head -n 1
}

get_tag_id() {
    local ORG_ID=$1
    local TAG_NAME=$2
    curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applicationCategories/organization/$ORG_ID" | \
    jq -r --arg n "$TAG_NAME" 'if type == "array" then .[] else .categories[]? end | select(.name==$n) | .id' | head -n 1
}

jq -c '.[]' "$EXPORT_FILE" | while read -r bundle; do
    ORG_NAME=$(echo "$bundle" | jq -r '.organization.name')
    TARGET_ORG_ID=$(get_org_id "$ORG_NAME")

    if [[ -z "$TARGET_ORG_ID" || "$TARGET_ORG_ID" == "null" ]]; then
        echo "  [NEW] Creating Org: $ORG_NAME"
        curl -u "$TARGET_USER" -s -X POST -H "Content-Type: application/json" -d "{\"name\":\"$ORG_NAME\"}" "$TARGET_URL/api/v2/organizations" > /dev/null
        TARGET_ORG_ID=$(get_org_id "$ORG_NAME")
    fi

    echo "Processing Org: $ORG_NAME"

    # --- TAG CREATION (Now with Valid Colors) ---
    echo "$bundle" | jq -c '.tags[]?' 2>/dev/null | while read -r tag; do
        T_NAME=$(echo "$tag" | jq -r '.name' | xargs)
        T_ID=$(get_tag_id "$TARGET_ORG_ID" "$T_NAME")
        
        if [[ -z "$T_ID" || "$T_ID" == "null" ]]; then
            echo "    - Creating Tag: $T_NAME"
            # IQ Color Palette: light-blue, dark-blue, light-green, dark-green, light-orange, dark-orange, light-red, dark-red, light-gray, dark-gray
            T_COLOR="dark-gray" 
            
            curl -u "$TARGET_USER" -s -X POST -H "Content-Type: application/json" \
                 -d "{\"name\":\"$T_NAME\", \"color\":\"$T_COLOR\"}" \
                 "$TARGET_URL/api/v2/applicationCategories/organization/$TARGET_ORG_ID" > /dev/null
            
            T_ID=$(get_tag_id "$TARGET_ORG_ID" "$T_NAME")
        fi
        [[ -n "$T_ID" && "$T_ID" != "null" ]] && echo "$T_NAME|$T_ID" >> "$GLOBAL_TAG_MAP"
    done

    # Refresh map
    MAP_JSON=$(jq -Rs 'split("\n") | map(select(length > 0) | split("|")) | map({(.[0]): .[1]}) | add' "$GLOBAL_TAG_MAP")

    # --- APP PROCESSING ---
    echo "$bundle" | jq -c '.applications[]?' | while read -r app; do
        APP_NAME=$(echo "$app" | jq -r '.name' | xargs)
        APP_PID=$(echo "$app" | jq -r '.publicId' | xargs)

        EXISTING_APP=$(curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applications?publicId=$APP_PID")
        INTERNAL_ID=$(echo "$EXISTING_APP" | jq -r '.applications[0].id // empty')

        if [[ -z "$INTERNAL_ID" || "$INTERNAL_ID" == "null" ]]; then
            PAYLOAD=$(jq -n --arg pid "$APP_PID" --arg name "$APP_NAME" --arg oid "$TARGET_ORG_ID" '{publicId: $pid, name: $name, organizationId: $oid}')
            INTERNAL_ID=$(curl -u "$TARGET_USER" -s -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$TARGET_URL/api/v2/applications" | jq -r '.id')
            echo -n "    - $APP_NAME: Created. "
        else
            echo -n "    - $APP_NAME: Sync. "
        fi

        TAG_APPLIED=0
        while read -r T_NAME_REQD; do
            if [[ -n "$T_NAME_REQD" ]]; then
                TID=$(echo "$MAP_JSON" | jq -r --arg n "$T_NAME_REQD" '.[$n] // empty')
                if [[ -n "$TID" && "$TID" != "null" ]]; then
                    curl -u "$TARGET_USER" -s -X POST "$TARGET_URL/api/v2/applicationCategories/application/$INTERNAL_ID/$TID" > /dev/null
                    ((TAG_APPLIED++))
                fi
            fi
        done < <(echo "$app" | jq -r '.applicationTags[]? | .tagName')
        
        [ "$TAG_APPLIED" -gt 0 ] && echo "Linked $TAG_APPLIED tags." || echo "No tags."
    done
done
