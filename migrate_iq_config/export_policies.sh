#!/bin/bash
source ./config.sh

EXPORT_FILE="${EXPORT_FILE_POLICIES:-./migration_data/policies_bundle.json}"
mkdir -p "$(dirname "$EXPORT_FILE")"
echo "[]" > "$EXPORT_FILE"

echo "--- STARTING POLICY EXPORT ---"

# Get all Organizations
ORGS_RAW=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/organizations")

echo "$ORGS_RAW" | jq -c '.organizations[]?' | while read -r org; do
    OID=$(echo "$org" | jq -r '.id')
    ONAME=$(echo "$org" | jq -r '.name')
    echo "Exporting policies for: $ONAME"

    # Fetch Policies
    RAW_POL_DATA=$(curl -u "$SOURCE_USER" -s "$SOURCE_URL/api/v2/policies/organization/$OID")
    
    # FLEX-PARSER: Handle both {"policies": []} and raw [] formats
    CLEAN_POLICIES=$(echo "$RAW_POL_DATA" | jq 'if type == "array" then . else .policies // [] end' 2>/dev/null || echo "[]")

    # Save to bundle - using a temporary file to prevent corruption
    jq --arg name "$ONAME" --argjson pols "$CLEAN_POLICIES" \
       '. += [{ orgName: $name, policies: $pols }]' "$EXPORT_FILE" > "$EXPORT_FILE.tmp" && mv "$EXPORT_FILE.tmp" "$EXPORT_FILE"
done

echo "--- POLICY EXPORT COMPLETE: $EXPORT_FILE ---"
