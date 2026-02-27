#!/bin/bash
source ./config.sh

EXPORT_FILE="./migration_data/full_migration_bundle.json"
mkdir -p "$(dirname "$EXPORT_FILE")"
echo "[]" > "$EXPORT_FILE"

echo "--- STARTING ROBUST EXPORT ---"

# 1. Get all Organizations
ORGS=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/organizations" | jq -c '.organizations[]?')

echo "$ORGS" | while read -r org; do
    [ -z "$org" ] && continue
    OID=$(echo "$org" | jq -r '.id')
    ONAME=$(echo "$org" | jq -r '.name')
    echo "Exporting: $ONAME"

    # 2. Export Tags for this Org (With Null Guards)
    TAGS=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/applicationCategories/organization/$OID" | \
           jq -c 'if type == "array" then . else .categories // [] end | 
           map({
               name: (if .name then (.name | gsub("[\\r\\n\\t]+"; "") | sub("^\\s+"; "") | sub("\\s+$"; "")) else "Unknown" end), 
               color: (.color // "#999999"), 
               description: (.description // "")
           })')

    # 3. Export Applications
    APPS_RAW=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/applications/organization/$OID" | jq -c '.applications[]?' 2>/dev/null)
    
    APPS_CLEAN="[]"
    if [ -n "$APPS_RAW" ]; then
        while read -r app; do
            [ -z "$app" ] && continue
            APP_ID=$(echo "$app" | jq -r '.id')
            
            # Fetch specific app details to get tag names
            # Use // [] to ensure we always have an array even if the call fails
            APP_DATA=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/applications/$APP_ID")
            
            APP_TAGS=$(echo "$APP_DATA" | jq -c '
                [ .applicationTags[]? | select(.tagName != null) | 
                {tagName: (.tagName | gsub("[\\r\\n\\t]+"; "") | sub("^\\s+"; "") | sub("\\s+$"; ""))} ]
            ' 2>/dev/null || echo "[]")
            
            # Build scrubbed app object
            CLEAN_APP=$(echo "$app" | jq --argjson tags "$APP_TAGS" '{publicId, name, applicationTags: $tags}')
            APPS_CLEAN=$(echo "$APPS_CLEAN" | jq --argjson a "$CLEAN_APP" '. += [$a]')
        done <<< "$APPS_RAW"
    fi

    # 4. Save to master bundle
    jq --argjson org "$org" --argjson apps "$APPS_CLEAN" --argjson tags "$TAGS" \
       '. += [{ organization: $org, applications: $apps, tags: $tags }]' "$EXPORT_FILE" > "$EXPORT_FILE.tmp" && mv "$EXPORT_FILE.tmp" "$EXPORT_FILE"
done

echo "--- EXPORT COMPLETE: $EXPORT_FILE ---"
