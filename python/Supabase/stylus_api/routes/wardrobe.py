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

wardrobe_bp = Blueprint("wardrobe", __name__)

# ===========================
# AI MODELS CONFIGURATION
# ===========================

# ---- Gemini Vision (expensive but good quality) ----
genai.configure(api_key=Config.GEM)
vision_model = genai.GenerativeModel("models/gemini-2.5-flash-lite")

# ---- Hugging Face Fallback ----
HF_API_KEY = Config.HUGGING_FACE  # Hugging Face API key (store in Config)
HF_CLIP_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"

def hf_clip_tag(image_bytes: bytes) -> dict:
    """
    Send the image to Hugging Face CLIP for basic clothing & color tagging.
    This is used as a cheaper fallback or async alternative to Gemini.
    """
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    try:
        response = requests.post(
            HF_CLIP_URL,
            headers=headers,
            files={"file": image_bytes},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            labels = result.get("labels", [])
            return {
                "category": labels[0] if len(labels) > 0 else None,
                "color": labels[1] if len(labels) > 1 else None,
                "material": labels[2] if len(labels) > 2 else None,
                "style_vibe": None,
                "fit": None
            }
        else:
            print(f"⚠️ HF CLIP returned {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"❌ HF CLIP error: {e}")
        return {}

def async_tag_and_update(item_id: str, image_bytes: bytes):
    """
    Run AI tagging in the background.
    1. Try Gemini
    2. If fails (quota or error), try Hugging Face CLIP
    3. Update Supabase only if new tags are present
    """

    # TRY: Gemini
    try:
        prompt = """
        Analyze this clothing item & return ONLY JSON:
        { category, color, occasion, material, style_vibe, fit }
        """
        gm_resp = vision_model.generate_content([{"mime_type": "image/jpeg", "data": image_bytes}, prompt])
        text = gm_resp.text.replace("```json", "").replace("```", "").strip()
        tags = json.loads(text)

    except Exception as gem_err:
        print(f"⚠️ Gemini tagging failed (async): {gem_err}")
        tags = hf_clip_tag(image_bytes)

    # If no tags returned, stop
    if not tags:
        print(f"ℹ️ No tags returned for item {item_id}, skipping update.")
        return

    update_data = {}
    if tags.get("category"): update_data["category"] = tags["category"]
    if tags.get("color"): update_data["color"] = tags["color"]
    # We store other tag fields in “tags” array
    update_data["tags"] = [tags.get("material"), tags.get("style_vibe"), tags.get("fit")]

    try:
        supabase.table("wardrobe_items") \
            .update(update_data).eq("id", item_id).execute()
        print(f"✅ Async tags updated for {item_id}")
    except Exception as e:
        print(f"❌ Failed DB update for {item_id}: {e}")

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
        item_id = new_item.get("id")

        # Kick off async tagging thread
        threading.Thread(target=async_tag_and_update, args=(item_id, file_data)).start()

        return jsonify({"item": new_item}), 201

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return jsonify({"error": str(e)}), 500

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
