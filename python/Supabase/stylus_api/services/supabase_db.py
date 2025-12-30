# DB RPCs / REST calls
# backend/stylus_api/services/supabase_db.py
import requests
from flask import current_app

def _headers():
  key = current_app.config["SUPABASE_SERVICE_ROLE_KEY"]
  return {
      "apikey": key,
      "Authorization": f"Bearer {key}",
      "Content-Type": "application/json",
  }

def create_wardrobe_item_row(payload: dict):
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/wardrobe_items"
    res = requests.post(url, headers=_headers(), json=[payload], params={"returning": "representation"})
    res.raise_for_status()
    return res.json()[0]

def get_user_wardrobe_rows(user_id: str):
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/wardrobe_items"
    params = {"user_id": f"eq.{user_id}", "select": "*", "order": "created_at.desc"}
    res = requests.get(url, headers=_headers(), params=params)
    res.raise_for_status()
    return res.json()

def create_event_row(payload: dict):
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/events"
    res = requests.post(url, headers=_headers(), json=[payload], params={"returning": "representation"})
    res.raise_for_status()
    return res.json()[0]

def get_user_events_rows(user_id: str):
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/events"
    params = {"user_id": f"eq.{user_id}", "select": "*", "order": "event_date.asc"}
    res = requests.get(url, headers=_headers(), params=params)
    res.raise_for_status()
    return res.json()
