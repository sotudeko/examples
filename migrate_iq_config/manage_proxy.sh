#!/bin/bash
source ./config.sh
while [[ "$#" -gt 0 ]]; do case $1 in --mode) MODE="$2"; shift ;; --url) URL="$2"; shift ;; --user) USER="$2"; shift ;; esac; shift; done
if [ "$MODE" == "export" ]; then
    curl -u "$USER" -s "$URL/api/v2/config/httpProxyServer" -o "$DATA_DIR/proxy.json"
else
    curl -u "$USER" -X PUT -H "Content-Type: application/json" "$URL/api/v2/config/httpProxyServer" -d @"$DATA_DIR/proxy.json"
fi
