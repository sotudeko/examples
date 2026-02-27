#!/bin/bash
source ./config.sh
while [[ "$#" -gt 0 ]]; do case $1 in --mode) MODE="$2"; shift ;; --url) URL="$2"; shift ;; --user) USER="$2"; shift ;; esac; shift; done

if [ "$MODE" == "export" ]; then
    # Fetch all roles and extract the roles array
    curl -u "$USER" -s "$URL/api/v2/roles" | jq '.roles | map(del(.id))' > "$DATA_DIR/roles.json"
else
    # Import roles one by one, skipping built-in roles that usually already exist
    jq -c '.[]' "$DATA_DIR/roles.json" | while read i; do
        curl -u "$USER" -X POST -H "Content-Type: application/json" "$URL/api/v2/roles" -d "$i"
    done
fi
