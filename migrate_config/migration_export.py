import json
import requests
import os
from requests.auth import HTTPBasicAuth

# --- CONFIG ---
SOURCE_URL = "http://localhost:8070"
AUTH = HTTPBasicAuth("admin", "admin123")
DATA_DIR = "./migration_data/orgs"

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(url):
    try:
        res = requests.get(url, auth=AUTH)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    print("--- STARTING TAG-RESOLVER EXPORT ---")
    
    orgs_payload = get_data(f"{SOURCE_URL}/api/v2/organizations")
    orgs = orgs_payload.get("organizations", []) if orgs_payload else []

    for org in orgs:
        o_id, o_name = org['id'], org['name']
        print(f"\nProcessing Org: {o_name}")

        # 1. Fetch Org-level Tag Definitions to build a Resolver Map
        # We need this because your app results only show tagId, not tagName
        tags_raw = get_data(f"{SOURCE_URL}/api/v2/applicationCategories/organization/{o_id}")
        org_tags_list = tags_raw if isinstance(tags_raw, list) else (tags_raw.get("categories", []) if tags_raw else [])
        
        # Create a dictionary: { "tagId": "tagName" }
        tag_resolver = {t['id']: t['name'] for t in org_tags_list if 'id' in t and 'name' in t}
        
        # 2. Fetch Apps (including categories)
        apps_url = f"{SOURCE_URL}/api/v2/applications/organization/{o_id}?includeCategories=true"
        apps_payload = get_data(apps_url)
        apps_raw = apps_payload.get("applications", []) if apps_payload else []
        
        apps_list = []
        for a in apps_raw:
            resolved_tag_names = []
            
            # 3. Resolve IDs to Names
            for tag_entry in a.get('applicationTags', []):
                t_id = tag_entry.get('tagId')
                if t_id in tag_resolver:
                    resolved_tag_names.append(clean(tag_resolver[t_id]))
            
            if resolved_tag_names:
                print(f"    - {a['name'].ljust(20)} Resolved Tags: {resolved_tag_names}")

            apps_list.append({
                "name": clean(a['name']),
                "publicId": clean(a['publicId']),
                "tags": resolved_tag_names
            })

        # 4. Save to JSON
        safe_name = "".join([c for c in o_name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        with open(f"{DATA_DIR}/{safe_name}.json", "w") as f:
            json.dump({
                "org_name": o_name, 
                "tags": [{"name": clean(t['name'])} for t in org_tags_list], 
                "apps": apps_list
            }, f, indent=2)

    print(f"\n--- EXPORT FINISHED ---")

if __name__ == "__main__":
    main()
    