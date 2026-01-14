from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..config import Config
from supabase import create_client

# 1. Keep the name simple (internal name, not a URL)
profile_bp = Blueprint("profile", __name__)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)

@profile_bp.route("/", methods=["GET", "POST"])
def manage_profile():
    user_id = get_current_user_id()
    
    # Check 1: Is the user logged in?
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    # PATH A: FETCHING DATA (GET)
    if request.method == "GET":
        try:
            # We use the official client for better error handling
            result = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                # Return a default if no profile exists yet
                return jsonify({"profile": {"display_name": "New User", "user_id": user_id}}), 200
            
            return jsonify({"profile": result.data[0]}), 200
        except Exception as e:
            print(f"❌ GET Error: {e}")
            return jsonify({"error": str(e)}), 500

    # PATH B: SAVING DATA (POST)
    if request.method == "POST":
        try:
            data = request.get_json()
            display_name = data.get('display_name', 'Anonymous')

            # Upsert: Update if ID exists, otherwise Insert
            result = supabase.table("user_profiles").upsert({
                "user_id": user_id,
                "display_name": display_name,
                "updated_at": "now()"
            }).execute()
            
            return jsonify({"message": "Saved", "profile": result.data[0]}), 201
        except Exception as e:
            print(f"❌ POST Error: {e}")
            return jsonify({"error": str(e)}), 500

    # SAFETY NET: If somehow it's not GET or POST
    return jsonify({"error": "Method not allowed"}), 405