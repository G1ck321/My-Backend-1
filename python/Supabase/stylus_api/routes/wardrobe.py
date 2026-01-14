# backend/stylus_api/routes/wardrobe.py - FIXED IMPORTS
from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc, upload_image  # ← FIXED: upload_image

wardrobe_bp = Blueprint("wardrobe", __name__)

@wardrobe_bp.route("/items", methods=["GET"])
def get_wardrobe():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    
    items = call_rpc("get_user_wardrobe", {"p_user_id": user_id})
    return jsonify({"items": items or []}),200

@wardrobe_bp.route("/items", methods=["POST"])
def create_wardrobe_item():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    # ... file validation ...

    try:
        # Read file data once
        file_data = file.read()
        
        # 1. Upload - Make sure this returns a string!
        uploaded_path = upload_image(user_id, file_data, file.filename)
        
        if not uploaded_path:
            return jsonify({"error": "Failed to upload to storage"}), 500

        # 2. Match your SQL function parameters exactly
        # REMOVE "created_at" unless your SQL function specifically asks for it!
        rpc_params = {
            "p_user_id": user_id,
            "p_image_url": uploaded_path,
            "p_category": request.form.get("category", "top"),
            "p_tags": request.form.getlist("tags[]") or []
        }

        item = call_rpc("create_wardrobe_item", rpc_params)
        return jsonify({"item": item}), 201
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500