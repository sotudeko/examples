import json
import requests
import os
import glob
from requests.auth import HTTPBasicAuth

# --- TARGET CONFIG ---
TARGET_URL = "http://localhost:8077"
AUTH = HTTPBasicAuth("admin", "admin123")
DATA_DIR = "./migration_data/orgs"

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(url):
    res = requests.get(url, auth=AUTH)
    return res.json() if res.status_code == 200 else None

def get_tag_id_on_the_fly(org_id, tag_name):
    raw_t = get_data(f"{TARGET_URL}/api/v2/applicationCategories/organization/{org_id}")
    if not raw_t: return None
    t_list = raw_t if isinstance(raw_t, list) else (raw_t.get("categories", []) if raw_t else [])
    
    normalized_target = clean(tag_name).lower()
    for t in t_list:
        if clean(t['name']).lower() == normalized_target:
            return t['id']
    return None

def main():
    print("--- STARTING FULL-OBJECT PUT IMPORT ---")
    
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
        
        # 1. Sync Org
        if o_name not in target_orgs:
            res = requests.post(f"{TARGET_URL}/api/v2/organizations", auth=AUTH, json={"name": o_name})
            target_org_id = res.json()['id']
            target_orgs[o_name] = target_org_id
        else:
            target_org_id = target_orgs[o_name]

        # 2. Sync Tags
        for t_req in org_data.get('tags', []):
            t_name = t_req['name']
            if not get_tag_id_on_the_fly(target_org_id, t_name):
                print(f"  Creating tag: {t_name}")
                requests.post(f"{TARGET_URL}/api/v2/applicationCategories/organization/{target_org_id}", 
                              auth=AUTH, json={"name": t_name, "color": "light-blue"})

        # 3. Sync Applications
        for app_export in org_data.get('apps', []):
            app_name, app_pid = app_export['name'], app_export['publicId']
            
            # Fetch existing app object from Target
            search_res = get_data(f"{TARGET_URL}/api/v2/applications?publicId={app_pid}")
            apps_found = search_res.get("applications", []) if search_res else []
            
            if not apps_found:
                print(f"    Creating App: {app_name}")
                res = requests.post(f"{TARGET_URL}/api/v2/applications", auth=AUTH, 
                                    json={"publicId": app_pid, "name": app_name, "organizationId": target_org_id})
                app_obj = res.json()
            else:
                app_obj = apps_found[0]

            # 4. CONSTRUCT THE PUT BODY
            # We need the full object to avoid 400 errors
            tag_payload = []
            for t_name in app_export.get('tags', []):
                t_id = get_tag_id_on_the_fly(target_org_id, t_name)
                if t_id:
                    tag_payload.append({"tagId": t_id})

            # Update the object with new tags
            app_obj['applicationTags'] = tag_payload
            
            # Perform the PUT to the specific app ID
            put_url = f"{TARGET_URL}/api/v2/applications/{app_obj['id']}"
            put_res = requests.put(put_url, auth=AUTH, json=app_obj)

            if put_res.status_code in [200, 204]:
                print(f"    - {app_name}: Successfully assigned {len(tag_payload)} tags.")
            else:
                print(f"    - {app_name}: FAILED assignment. Status: {put_res.status_code}")
                print(f"      Response: {put_res.text}")

if __name__ == "__main__":
    main()
    