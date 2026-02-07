# backend/stylus_api/routes/wardrobe.py
from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc, upload_image
from .profile import supabase
import google.generativeai as genai
import json
import random
import threading
import requests
from ..config import Config
import base64

wardrobe_bp = Blueprint("wardrobe", __name__)

# ===========================
# AI MODELS CONFIGURATION
# ===========================

# ---- Gemini Vision (expensive but good quality) ----
genai.configure(api_key=Config.GEM)
vision_model = genai.GenerativeModel("models/gemini-2.5-flash-lite")

# ---- Hugging Face Fallback ----
HF_API_KEY = Config.HUGGING_FACE  # Hugging Face API key (store in Config)
HF_CLIP_URL = "https://router.huggingface.co/hf-inference/models/openai/clip-vit-base-patch32"

def hf_clip_tag(image_bytes: bytes) -> dict:
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "inputs": {
            "image": image_b64,
            "candidate_labels": [
                "t-shirt", "shirt", "jacket", "hoodie",
                "jeans", "trousers", "shorts",
                "sneakers", "boots", "sandals",
                "black", "white", "blue", "red", "green",
                "cotton", "denim", "leather",
                "streetwear", "formal", "casual",
                "oversized", "slim fit"
            ]
        }
    }

    r = requests.post(HF_CLIP_URL, headers=headers, json=payload, timeout=30)

    if r.status_code != 200:
        print(f"⚠️ HF CLIP returned {r.status_code} - {r.text}")
        return {}

    result = r.json()

    return {
        "category": result["labels"][0] if result["labels"] else None,
        "color": next((l for l in result["labels"] if l in ["black","white","blue","red","green"]), None),
        "material": next((l for l in result["labels"] if l in ["cotton","denim","leather"]), None),
        "style_vibe": next((l for l in result["labels"] if l in ["streetwear","formal","casual"]), None),
        "fit": next((l for l in result["labels"] if l in ["oversized","slim fit"]), None),
    }

def async_tag_and_update(item_id: str, image_bytes: bytes):
    # 1. Try Gemini (Use the stable 1.5 Flash)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        # Added a system instruction to force strict JSON
        prompt = "Return ONLY JSON for this clothing: {category, color, material, style_vibe, fit}"
        gm_resp = model.generate_content([{"mime_type": "image/jpeg", "data": image_bytes}, prompt])
        
        # Cleaner JSON extraction
        clean_text = gm_resp.text.strip().lstrip('```json').rstrip('```').strip()
        tags = json.loads(clean_text)
        print(f"✅ Tags generated: {tags}")
    except Exception as e:
        print(f"Fallback to HF due to: {e}")
        tags = hf_clip_tag(image_bytes)

    # 2. Update Database
    if tags:
        # Map the AI response to your database structure
        update_payload = {
            "category": tags.get("category"),
            "color": tags.get("color"),
            "tags": [tags.get("material"), tags.get("style_vibe"), tags.get("fit")]
        }
        res = supabase.table("wardrobe_items").update(update_payload).eq("id", item_id).execute()
        print(f"💾 DB Update result: {res}")

# ===========================
# ROUTES
# ===========================

@wardrobe_bp.route("/items", methods=["GET"])
def get_wardrobe():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    items = call_rpc("get_user_wardrobe", {"p_user_id": user_id})
    if items is None:
        print("❌ RPC returned None - check function exist!")
        return jsonify({"items": [], "debug_msg": "no data"}), 200

    return jsonify({"items": items}), 200

@wardrobe_bp.route("/items/<item_id>", methods=["DELETE"])
def delete_wardrobe_item(item_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    try:
        supabase.table("wardrobe_items") \
            .delete().eq("id", item_id).eq("user_id", user_id).execute()
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({"error": str(e)}), 500

@wardrobe_bp.route("/items", methods=["POST"])
def create_wardrobe_item():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        file_data = file.read()
        uploaded_path = upload_image(user_id, file_data, file.filename)

        # Insert initial row with minimal defaults
        rpc_params = {
            "p_user_id": user_id,
            "p_image_url": uploaded_path,
            "p_category": request.form.get("category", "top"),
            "p_tags": [None, None, None]
        }
        new_item = call_rpc("create_wardrobe_item", rpc_params)
        if not new_item:
            return jsonify({"error": "Failed to create item"}), 500

        item_id = new_item.get("id")

        # Kick off async tagging thread
        threading.Thread(target=async_tag_and_update, args=(item_id, file_data)).start()

        return jsonify({"item": new_item}), 201

    except Exception as e:
        err_str = str(e)
        print(f"❌ Upload Error: {err_str}")

        # Handle common Supabase 409 duplicate
        if "statusCode" in err_str and "409" in err_str:
            return jsonify({
                "error": "Item already exists",
                "details": err_str
            }), 409

        # Generic fallback
        return jsonify({"error": err_str}), 500

@wardrobe_bp.route("/simple-ootd", methods=["GET"])
def get_simple_ootd():
    user_id = get_current_user_id()
    res = supabase.table("wardrobe_items").select("*").eq("user_id", user_id).execute()
    items = res.data or []

    tops    = [i for i in items if i["category"]=="top"]
    bottoms = [i for i in items if i["category"]=="bottom"]
    shoes   = [i for i in items if i["category"]=="shoes"]
    sel = []
    if tops:    sel.append(random.choice(tops))
    if bottoms: sel.append(random.choice(bottoms))
    if shoes:   sel.append(random.choice(shoes))

    ootd = [
        {"id": i["id"], "type": i["category"], "color": i.get("color","Neutral"), "image_url": i["image_url"]}
        for i in sel
    ]
    return jsonify(ootd)

@wardrobe_bp.route("/insights/colors", methods=["GET"])
def get_color_insights():
    user_id = get_current_user_id()
    res = supabase.rpc("get_color_distribution", {"p_user_id": user_id}).execute()
    return jsonify(res.data)

@wardrobe_bp.route("/items/favorite", methods=["POST"])
def toggle_favorite():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    item_id = data.get("item_id")
    is_favorite = data.get("is_favorite", False)
    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    try:
        supabase.table("wardrobe_items") \
            .update({"is_favorite": is_favorite}) \
            .eq("id", item_id).eq("user_id", user_id).execute()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@wardrobe_bp.route("/repair-null-tags", methods=["GET"])
def repair_tags():
    user_id = get_current_user_id()
    # 1. Fetch items with missing tags
    res = supabase.table("wardrobe_items").select("*").eq("user_id", user_id).execute()
    items = res.data or []
    
    repaired_count = 0
    for item in items:
        if not item.get("color") or item.get("color") == "Neutral":
            # 2. Get the image from Supabase Storage to re-tag it
            # (This assumes image_url is the path in your bucket)
            img_res = supabase.storage.from_("wardrobe-images").download(item["image_url"])
            
            # 3. Trigger the tagging
            threading.Thread(target=async_tag_and_update, args=(item["id"], img_res)).start()
            repaired_count += 1
            
    return jsonify({"msg": f"Attempting to repair {repaired_count} items"}), 200