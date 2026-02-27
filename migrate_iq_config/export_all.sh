#!/bin/bash
source ./config.sh
mkdir -p "$DATA_DIR"

echo "--- STARTING FULL EXPORT ---"
# ./manage_base_url.sh      --mode export --url "$SOURCE_URL" --user "$SOURCE_USER"
# ./manage_proxy.sh         --mode export --url "$SOURCE_URL" --user "$SOURCE_USER"
# ./manage_mail.sh          --mode export --url "$SOURCE_URL" --user "$SOURCE_USER"
# ./manage_policies.sh      --mode export --url "$SOURCE_URL" --user "$SOURCE_USER"
# ./manage_roles.sh         --mode export --url "$SOURCE_URL" --user "$SOURCE_USER"
./export_orgs_apps_tags.sh
echo "--- EXPORT COMPLETE ---"
