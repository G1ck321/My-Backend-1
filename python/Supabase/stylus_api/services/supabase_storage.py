# Storage helpers
# backend/stylus_api/services/supabase_storage.py
from storage3 import create_client
from flask import current_app
from datetime import datetime

def _storage_client():
    url = current_app.config["SUPABASE_URL"].rstrip("/") + "/storage/v1"
    key = current_app.config["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apiKey": key, "Authorization": f"Bearer {key}"}
    return create_client(url, headers, is_async=False)

def upload_wardrobe_image(user_id: str, file_obj, filename: str) -> str:
    """
    Uploads file to bucket 'wardrobe-images' at path '<user_id>/<timestamp>-<filename>'
    Returns the path string.
    """
    client = _storage_client()
    bucket = client.from_("wardrobe-images")  # create this bucket in Supabase UI[web:186][web:198]
    safe_name = filename.replace(" ", "_")
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = f"{user_id}/{ts}-{safe_name}"
    bucket.upload(path, file_obj)
    return path
