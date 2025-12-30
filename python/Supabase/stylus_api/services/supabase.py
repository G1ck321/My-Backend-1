# backend/stylus_api/services/supabase.py - COMPLETE WITH get_table
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
    """Call Supabase RPC function"""
    url = f"{current_app.config['SUPABASE_URL']}/rpc/{function_name}"
    res = requests.post(url, headers=supabase_headers(), json=params)
    if res.status_code >= 400:
        print(f"❌ RPC {function_name} failed: {res.status_code} {res.text}")
        return None
    return res.json()

def get_table(table: str, filters: Dict[str, str] = None) -> List[Dict]:
    """Query table with filters (used by profile.py)"""
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/{table}"
    params: Dict[str, str] = {"select": "*"}
    
    if filters:
        for key, value in filters.items():
            params[f"{key}"] = f"eq.{value}"
    
    res = requests.get(url, headers=supabase_headers(), params=params)
    if res.status_code >= 400:
        print(f"❌ get_table {table} failed: {res.status_code}")
        return []
    
    return res.json()

def storage_client():
    """Supabase Storage client"""
    url = f"{current_app.config['SUPABASE_URL']}/storage/v1"
    key = current_app.config["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    return create_client(url, headers, is_async=False)

def upload_image(user_id: str, file_bytes: bytes, filename: str) -> str:
    """Upload to wardrobe-images/{user_id}/{filename}"""
    try:
        client = storage_client()
        bucket = client.from_("wardrobe-images")
        
        # Sanitize filename
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        path = f"{user_id}/{safe_filename}"
        
        # Upload
        bucket.upload(path, file_bytes)
        print(f"✅ Uploaded to: wardrobe-images/{path}")
        
        return path
    except Exception as e:
        print(f"❌ Storage upload failed: {str(e)}")
        raise e
