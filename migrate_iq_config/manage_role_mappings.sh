#!/bin/bash
source ./config.sh
while [[ "$#" -gt 0 ]]; do case $1 in --mode) MODE="$2"; shift ;; --url) URL="$2"; shift ;; --user) USER="$2"; shift ;; esac; shift; done
ID=$(curl -u "$USER" -s "$URL/api/v2/organizations" | jq -r '.organizations[] | select(.name=="Root Organization") | .id')
if [ "$MODE" == "export" ]; then
    curl -u "$USER" -s "$URL/api/v2/organizations/$ID/roleMembers" -o "$DATA_DIR/role_mappings.json"
else
    curl -u "$USER" -X PUT -H "Content-Type: application/json" "$URL/api/v2/organizations/$ID/roleMembers" -d @"$DATA_DIR/role_mappings.json"
fi
