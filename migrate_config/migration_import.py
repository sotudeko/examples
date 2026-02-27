import json
import requests
import os
import glob
from requests.auth import HTTPBasicAuth

# --- TARGET CONFIG ---
TARGET_URL = "http://localhost:8077"
AUTH = HTTPBasicAuth("admin", "admin123")
DATA_DIR = "./migration_data/orgs"

# Your server's strictly supported colors
SUPPORTED_COLORS = [
    "light-red", "light-green", "light-blue", "light-purple",
    "dark-red", "dark-green", "dark-blue", "dark-purple",
    "orange", "yellow"
]

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(url):
    res = requests.get(url, auth=AUTH)
    return res.json() if res.status_code == 200 else None

def get_tag_map(org_id):
    raw_t = get_data(f"{TARGET_URL}/api/v2/applicationCategories/organization/{org_id}")
    if not raw_t: return {}
    t_list = raw_t if isinstance(raw_t, list) else (raw_t.get("categories", []) if raw_t else [])
    return {clean(t['name']).lower(): t['id'] for t in t_list}

def main():
    print("--- STARTING PALETTE-AWARE IMPORT ---")
    
    orgs_payload = get_data(f"{TARGET_URL}/api/v2/organizations")
    if not orgs_payload:
        print("Error: Target server unreachable.")
        return
    target_orgs = {o['name']: o['id'] for o in orgs_payload.get("organizations", [])}

    for file_path in sorted(glob.glob(f"{DATA_DIR}/*.json")):
        with open(file_path, "r") as f:
            org_data = json.load(f)
        
        o_name = org_data['org_name']
        if o_name == "Root Organization": continue
        
        print(f"\nProcessing Org: {o_name}")
        
        if o_name not in target_orgs:
            res = requests.post(f"{TARGET_URL}/api/v2/organizations", auth=AUTH, json={"name": o_name})
            target_org_id = res.json()['id']
            target_orgs[o_name] = target_org_id
        else:
            target_org_id = target_orgs[o_name]

        # 1. CREATE TAGS WITH VALID COLORS
        for t_req in org_data.get('tags', []):
            t_name = t_req['name']
            
            current_map = get_tag_map(target_org_id)
            if clean(t_name).lower() not in current_map:
                # Check if the exported color is supported, else use light-blue
                exported_color = t_req.get('color', '').lower()
                final_color = exported_color if exported_color in SUPPORTED_COLORS else "light-blue"
                
                print(f"  Creating tag '{t_name}' with color '{final_color}'...")
                
                payload = {
                    "name": t_name,
                    "description": f"Migrated: {t_name}",
                    "color": final_color
                }
                
                res = requests.post(
                    f"{TARGET_URL}/api/v2/applicationCategories/organization/{target_org_id}", 
                    auth=AUTH, 
                    json=payload
                )
                
                if res.status_code not in [200, 201, 204]:
                    print(f"  FAILED: ({res.status_code}) {res.text}")
            else:
                print(f"  Tag '{t_name}' already exists.")

        # 2. REFRESH MAP & LINK
        active_map = get_tag_map(target_org_id)

        for app in org_data.get('apps', []):
            app_name, app_pid = app['name'], app['publicId']
            
            find_app = get_data(f"{TARGET_URL}/api/v2/applications?publicId={app_pid}")
            apps_found = find_app.get("applications", []) if find_app else []
            
            if not apps_found:
                res = requests.post(f"{TARGET_URL}/api/v2/applications", auth=AUTH, 
                                    json={"publicId": app_pid, "name": app_name, "organizationId": target_org_id})
                app_id = res.json()['id']
            else:
                app_id = apps_found[0]['id']

            applied = 0
            for req_tag_name in app.get('tags', []):
                lookup = clean(req_tag_name).lower()
                if lookup in active_map:
                    t_id = active_map[lookup]
                    requests.post(f"{TARGET_URL}/api/v2/applicationCategories/application/{app_id}/{t_id}", auth=AUTH)
                    applied += 1
            
            if len(app.get('tags', [])) > 0:
                print(f"    - {app_name}: Linked {applied}/{len(app.get('tags', []))} tags.")

if __name__ == "__main__":
    main()

    