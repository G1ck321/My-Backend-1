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
    return jsonify({"items": items or []})

@wardrobe_bp.route("/items", methods=["POST"])
def create_wardrobe_item():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400

    file = request.files["file"]
    if not file.filename or file.filename == "":
        return jsonify({"error": "invalid file"}), 400

    try:
        # 1. Upload image
        image_path = upload_image(user_id, file.read(), file.filename)
        
        # 2. Create DB record
        category = request.form.get("category", "top")
        tags = request.form.getlist("tags[]") or []
        
        item = call_rpc("create_wardrobe_item", {
            "p_user_id": user_id,
            "p_image_path": image_path,
            "p_category": category,
            "p_tags": tags
        })
        
        return jsonify({"item": item}), 201
        
    except Exception as e:
        print(f"❌ Create item failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
