# backend/stylus_api/routes/wardrobe.py - FIXED IMPORTS
from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc, upload_image  # ← FIXED: upload_image
from .profile import supabase   
wardrobe_bp = Blueprint("wardrobe", __name__)

@wardrobe_bp.route("/items", methods=["GET"])
def get_wardrobe():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    
    # 1. Call the RPC
    items = call_rpc("get_user_wardrobe", {"p_user_id": user_id})
    
    # 2. DEBUG PRINT: See the actual data in your Render/Terminal logs
    print(f"📦 Data from DB: {items}") 
    
    # 3. Check if it's None or Empty
    if items is None:
        print("❌ RPC returned None - Check if function 'get_user_wardrobe' exists!")
        return jsonify({"items": [], "debug_msg": "RPC returned None"}), 200

    return jsonify({"items": items}), 200

@wardrobe_bp.route("/items", methods=["POST"])
def create_wardrobe_item():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    # Check for file BEFORE the try block
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"] # <--- 'file' is now defined in this scope
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read the content into a variable immediately
        file_data = file.read() 
        file_name = file.filename

        # Pass the DATA, not the file object, to the service
        uploaded_path = upload_image(user_id, file_data, file_name)
        
        # Now use p_image_url to match your SQL function exactly
        rpc_params = {
            "p_user_id": user_id,
            "p_image_url": uploaded_path,
            "p_category": request.form.get("category", "top"),
            "p_tags": request.form.getlist("tags[]") or ["blue", "summer"]
        }

        print(f"🚀 Calling RPC with: {rpc_params}")
        item = call_rpc("create_wardrobe_item", rpc_params)
        
        return jsonify({"item": item}), 201
        
    except Exception as e:
        # If 'file' was the problem, it will be caught here
        print(f"❌ Upload Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
@wardrobe_bp.route('/simple-ootd', methods=['GET'])
def get_simple_ootd():
    user_id = get_current_user_id()
    
    # 1. Fetch items from Supabase
    # In a real scenario, your Rule-Based Engine would run here.
    # For now, let's return a basic set of items to fix the 404.
    items = supabase.table('wardrobe_items').select('*').eq('user_id', user_id).limit(3).execute()
    
    # Format to match your Frontend OutfitItem interface
    ootd = []
    for item in items.data:
        ootd.append({
            "id": item['id'],
            "type": item['category'],
            "color": item.get('color', 'Neutral'),
            "image_url": item['image_url']
        })
        
    return jsonify(ootd)
@wardrobe_bp.route("/log-wear", methods=["POST"])
def log_wear():
    user_id = get_current_user_id()
    data = request.get_json()
    item_ids = data.get("item_ids") # Array of IDs worn

    # Log to the 'outfit_logs' table for Style Insights
    supabase.table("outfit_logs").insert({
        "user_id": user_id,
        "items": item_ids,
        "weather_context": get_weather().get_json()
    }).execute()
    
    return jsonify({"status": "logged"})