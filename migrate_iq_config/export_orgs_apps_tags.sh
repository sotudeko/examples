#!/bin/bash
source ./config.sh

EXPORT_FILE="${EXPORT_FILE:-./migration_data/full_migration_bundle.json}"
ALL_TAGS_FILE="./migration_data/all_tags_lookup.json"
mkdir -p "$(dirname "$EXPORT_FILE")"

echo "--- STARTING GLOBAL-AWARE EXPORT ---"

# 1. First Pass: Collect EVERY tag from EVERY org
echo "Collecting global tag definitions..."
ORGS_RAW=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/organizations")
echo "[]" > "$ALL_TAGS_FILE"

echo "$ORGS_RAW" | jq -c '.organizations[]' | while read -r org; do
    OID=$(echo "$org" | jq -r '.id')
    # Fetch tags and handle both object and array formats
    RAW_TAG_DATA=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/applicationCategories/organization/$OID")
    
    # Flex-parse: if it's an array, use it; if it has a .categories key, use that.
    echo "$RAW_TAG_DATA" | jq 'if type == "array" then . else .categories // [] end' > tmp_tags.json
    
    # Merge into our global lookup list
    jq -s '.[0] + .[1]' "$ALL_TAGS_FILE" tmp_tags.json > tmp_combined.json && mv tmp_combined.json "$ALL_TAGS_FILE"
done

# Deduplicate the global tags list by ID to keep it clean
jq 'unique_by(.id)' "$ALL_TAGS_FILE" > tmp_unique.json && mv tmp_unique.json "$ALL_TAGS_FILE"

# 2. Second Pass: Export Orgs and enrich Apps
echo "[]" > "$EXPORT_FILE"
echo "$ORGS_RAW" | jq -c '.organizations[]' | while read -r org; do
    ORG_ID=$(echo "$org" | jq -r '.id')
    ORG_NAME=$(echo "$org" | jq -r '.name')
    echo "Exporting: $ORG_NAME"

    # Get local tags for this org (Flex-parse again)
    LOCAL_TAG_DATA=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/applicationCategories/organization/$ORG_ID")
    LOCAL_TAGS=$(echo "$LOCAL_TAG_DATA" | jq 'if type == "array" then . else .categories // [] end')

    # Get Apps
    APPS_RAW=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/applications/organization/$ORG_ID")

    # Enrich Apps using the GLOBAL tag file
    ENRICHED_APPS=$(echo "$APPS_RAW" | jq --argjson global_tags "$(cat "$ALL_TAGS_FILE")" '
      .applications // [] | map(. as $app | $app + {
        applicationTags: (if $app.applicationTags then 
          $app.applicationTags | map(. as $at | $at + {
            tagName: ($global_tags | map(select(.id == $at.tagId)) | .[0].name // "Unknown")
          })
        else [] end)
      })
    ')

    # Save to bundle
    jq --argjson org "$org" --argjson tags "$LOCAL_TAGS" --argjson apps "$ENRICHED_APPS" \
       '. += [{ organization: $org, tags: $tags, applications: $apps }]' "$EXPORT_FILE" > "$EXPORT_FILE.tmp" && mv "$EXPORT_FILE.tmp" "$EXPORT_FILE"
done

rm -f tmp_tags.json tmp_combined.json tmp_unique.json
echo "--- EXPORT COMPLETE: $EXPORT_FILE ---"
