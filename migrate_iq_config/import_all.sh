#!/bin/bash
source ./config.sh

echo "--- STARTING FULL IMPORT ---"
# ./manage_base_url.sh      --mode import --url "$TARGET_URL" --user "$TARGET_USER"
# ./manage_proxy.sh         --mode import --url "$TARGET_URL" --user "$TARGET_USER"
# ./manage_mail.sh          --mode import --url "$TARGET_URL" --user "$TARGET_USER"
# ./manage_roles.sh         --mode import --url "$TARGET_URL" --user "$TARGET_USER"
./import_orgs_apps_tags.sh
# ./import_policies.sh
echo "--- IMPORT COMPLETE ---"
