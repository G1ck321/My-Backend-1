from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import get_table

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/me/profile", methods=["GET"])
def get_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    
    profile = get_table("user_profiles", {"user_id": user_id})
    return jsonify({"profile": profile[0] if profile else None})

@profile_bp.route("/me/profile", methods=["PUT"])
def update_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.get_json() or {}
    profile_data = {
        "user_id": user_id,
        **data
    }
    
    url = f"{current_app.config['SUPABASE_URL']}/rest/v1/user_profiles?user_id=eq.{user_id}"
    res = requests.patch(url, headers=supabase_headers(), json=[profile_data])
    
    if res.status_code == 200 and res.json():
        return jsonify({"profile": res.json()[0]}), 200
    elif res.status_code == 404:
        # Create if not exists
        url = f"{current_app.config['SUPABASE_URL']}/rest/v1/user_profiles"
        res = requests.post(url, headers=supabase_headers(), json=[profile_data])
        return jsonify({"profile": res.json()[0]}), 201
    
    return jsonify({"error": "failed to update profile"}), 500
