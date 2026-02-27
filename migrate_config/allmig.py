import json
import requests
from requests.auth import HTTPBasicAuth

# --- SETTINGS ---
SOURCE_URL = "http://localhost:8070"
TARGET_URL = "http://localhost:8077"
SOURCE_AUTH = HTTPBasicAuth("admin", "admin123")
TARGET_AUTH = HTTPBasicAuth("admin", "admin123")

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(url, auth):
    res = requests.get(url, auth=auth)
    return res.json() if res.status_code == 200 else None

def main():
    print("--- 1. EXPORTING FROM SOURCE ---")
    orgs = get_data(f"{SOURCE_URL}/api/v2/organizations", SOURCE_AUTH).get("organizations", [])
    bundle = []

    for org in orgs:
        o_id, o_name = org['id'], org['name']
        print(f"  Fetching Org: {o_name}")

        # Fetch Tags
        tags_raw = get_data(f"{SOURCE_URL}/api/v2/applicationCategories/organization/{o_id}", SOURCE_AUTH)
        tags = tags_raw if isinstance(tags_raw, list) else tags_raw.get("categories", [])
        
        # Fetch Apps
        apps_raw = get_data(f"{SOURCE_URL}/api/v2/applications/organization/{o_id}", SOURCE_AUTH).get("applications", [])
        apps = []
        for a in apps_raw:
            detail = get_data(f"{SOURCE_URL}/api/v2/applications/{a['id']}", SOURCE_AUTH)
            apps.append({
                "name": clean(a['name']),
                "publicId": clean(a['publicId']),
                "tags": [clean(t['tagName']) for t in detail.get("applicationTags", []) if t.get("tagName")]
            })
        
        bundle.append({
            "name": o_name,
            "tags": [{"name": clean(t['name'])} for t in tags],
            "apps": apps
        })

    print("\n--- 2. IMPORTING TO TARGET ---")
    target_orgs = {o['name']: o['id'] for o in get_data(f"{TARGET_URL}/api/v2/organizations", TARGET_AUTH).get("organizations", [])}

    for org in bundle:
        # Create Org if missing
        if org['name'] not in target_orgs:
            print(f"Creating Org: {org['name']}")
            res = requests.post(f"{TARGET_URL}/api/v2/organizations", auth=TARGET_AUTH, json={"name": org['name']})
            target_org_id = res.json()['id']
        else:
            target_org_id = target_orgs[org['name']]

        # Sync Tags
        print(f"Processing {org['name']}...")
        for t in org['tags']:
            requests.post(f"{TARGET_URL}/api/v2/applicationCategories/organization/{target_org_id}", 
                          auth=TARGET_AUTH, json={"name": t['name'], "color": "gray"})
        
        # Build Tag ID Map
        raw_t = get_data(f"{TARGET_URL}/api/v2/applicationCategories/organization/{target_org_id}", TARGET_AUTH)
        t_list = raw_t if isinstance(raw_t, list) else raw_t.get("categories", [])
        tag_map = {clean(t['name']): t['id'] for t in t_list}

        # Sync Apps and Link Tags
        for app in org['apps']:
            # Find/Create App
            find_app = get_data(f"{TARGET_URL}/api/v2/applications?publicId={app['publicId']}", TARGET_AUTH).get("applications", [])
            if not find_app:
                res = requests.post(f"{TARGET_URL}/api/v2/applications", auth=TARGET_AUTH, 
                                    json={"publicId": app['publicId'], "name": app['name'], "organizationId": target_org_id})
                app_id = res.json()['id']
            else:
                app_id = find_app[0]['id']

            # Apply Tags
            applied = 0
            for t_name in app['tags']:
                if t_name in tag_map:
                    requests.post(f"{TARGET_URL}/api/v2/applicationCategories/application/{app_id}/{tag_map[t_name]}", auth=TARGET_AUTH)
                    applied += 1
            print(f"    - {app['name']}: Linked {applied} tags.")

if __name__ == "__main__":
    main()
    