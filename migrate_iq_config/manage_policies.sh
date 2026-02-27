#!/bin/bash
source ./config.sh
while [[ "$#" -gt 0 ]]; do case $1 in --mode) MODE="$2"; shift ;; --url) URL="$2"; shift ;; --user) USER="$2"; shift ;; esac; shift; done

# Resolve Root ID for the specific server
ID=$(curl -u "$USER" -s "$URL/api/v2/organizations" | jq -r '.organizations[] | select(.name=="Root Organization") | .id')

if [ "$MODE" == "export" ]; then
    echo "  [EXPORT] Fetching Policies from Root: $ID"
    # Fetch policies and strip 'id' from the top-level and policy objects
    # We also strip 'ownerId' so the target server can assign its own Root ID as the owner
    curl -u "$USER" -s "$URL/rest/policy/organization/$ID/export" | jq 'del(.id, .ownerId) | .policies |= map(del(.id, .ownerId))' > "$DATA_DIR/policies.json"
    echo "  [SUCCESS] Policies exported (IDs stripped)."
else
    echo "  [IMPORT] Pushing Policies to Root: $ID"
    # Import the cleaned file to the Target Root
    curl -u "$USER" -X POST -H "Content-Type: application/json" "$URL/rest/policy/organization/$ID/import" -d @"$DATA_DIR/policies.json"
    echo "  [SUCCESS] Policies imported."
fi
