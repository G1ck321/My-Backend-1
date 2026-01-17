# backend/stylus_api/services/supabase.py - COMPLETE
import requests
from flask import current_app
from storage3 import create_client
from typing import Any, Dict, List

def supabase_headers():
    key = current_app.config["SUPABASE_SERVICE_ROLE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

def call_rpc(function_name: str, params: dict) -> Any:
    # 1. Ensure the URL is correct with /rest/v1/
    url = f"{current_app.config['SUPABASE_URL'].rstrip('/')}/rest/v1/rpc/{function_name}"
    
    try:
        # 2. Use requests.post NOT requests.get
        # 3. Use json=params to send data in the body
    # Use the /rest/v1/rpc/ path
    
    
        res = requests.post(
            url, 
            headers=supabase_headers(), 
            json=params, 
            timeout=10
        )
        
        if res.status_code >= 400:
            # This will help you see exactly what the DB is complaining about
            print(f"❌ RPC {function_name} Error: {res.status_code} - {res.text}")
            return None
            
        return res.json()
    except Exception as e:
        print(f"❌ RPC Connection Error: {str(e)}")
        return None
def get_table(table: str, filters: Dict[str, str] = None) -> List[Dict]:
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/{table}"
    print(f"📡 Requesting URL: {url}")
    params: Dict[str, str] = {"select": "*"}
    if filters:
        for key, value in filters.items():
            params[f"{key}"] = f"eq.{value}"
    res = requests.get(url, headers=supabase_headers(), params=params)
    if res.status_code >= 400:
        print(f"❌ get_table {table}: {res.status_code}")
        return []
    return res.json()

def upload_image(user_id: str, file_bytes: bytes, filename: str) -> str:
    """Upload to wardrobe-images/{user_id}/{filename} - SERVICE ROLE ONLY"""
    try:
        url = f"{current_app.config['SUPABASE_URL']}/storage/v1"
        key = current_app.config["SUPABASE_SERVICE_ROLE_KEY"]
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        client = create_client(url, headers, is_async=False)
        bucket = client.from_("wardrobe-images")
        
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        path = f"{user_id}/{safe_filename}"
        
        bucket.upload(path, file_bytes)
        print(f"✅ Uploaded: wardrobe-images/{path}")
        return path
# def upload_image(user_id, file_bytes, filename):
#     # Create a unique path: user_id/timestamp_filename
#     from datetime import datetime
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     storage_path = f"{user_id}/{timestamp}_{filename}"
#     try:
#         # Use the supabase client to upload to your bucket
#         # Note: 'supabase' must be initialized in this file or imported
#         res = supabase.storage.from_("wardrobe-images").upload(
#             path=storage_path,
#             file=file_bytes, # This is the raw data
#             file_options={"content-type": "image/png"} # Or detect type
#         )

#         # Supabase returns the path on success
#         return storage_path
    except Exception as e:
        print(f"❌ Storage upload failed: {str(e)}")
        raise e
