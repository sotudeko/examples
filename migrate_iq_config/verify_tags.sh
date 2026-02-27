#!/bin/bash
source config.sh

curl -u "$TARGET_USER" -s "$TARGET_URL/api/v2/applications" | jq '[.applications[] | {name: .name, tags: (.applicationTags | length)}] | sort_by(.tags) | reverse'