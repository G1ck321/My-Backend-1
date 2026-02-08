# backend/stylus_api/routes/wardrobe.py
from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc, upload_image
from storage3.exceptions import StorageApiError
from .profile import supabase
import google.generativeai as genai
import json, random, time, threading, requests, base64
from ..config import Config
from PIL import Image
from io import BytesIO

from concurrent.futures import ThreadPoolExecutor, as_completed

wardrobe_bp = Blueprint("wardrobe", __name__)

# ===========================
# AI MODELS CONFIGURATION
# ===========================

# ---- Gemini Vision (expensive but good quality) ----
genai.configure(api_key=Config.GEM)
vision_model = genai.GenerativeModel("models/gemini-1.5-flash")

# ---- Hugging Face Fallback ----
HF_API_KEY = Config.HUGGING_FACE

# Hugging Face CLIP Zero-Shot Classificatio
HF_CLIP_URL = "https://router.huggingface.co/hf-inference/models/openai/clip-vit-base-patch32"

HF_HEADERS = {"Authorization": f"Bearer {Config.HUGGING_FACE}"}

# Predefined labels focused on student wardrobes
STUDENT_LABELS = {
    "top": ["oversized hoodie", "university sweatshirt", "graphic tee", "flannel shirt", "polo shirt", "blazer", "crop top"],
    "bottom": ["baggy jeans", "cargo pants", "sweatpants", "biker shorts", "denim skirt", "chino pants"],
    "accessory": ["backpack", "tote bag", "beanie", "lanyard", "smartwatch", "silver ring", "gold ring"],
    "shoes": ["white sneakers", "running shoes", "slides", "doc martens", "loafers", "canvas high-tops"]
}

# --------------------------
# HELPER FUNCTIONS
# --------------------------
# Retry configuration
MAX_HF_RETRIES = 3
BASE_RETRY_DELAY = 2  # seconds (will use exponential backoff)
NOVITA_TAGGING_URL = "https://api.novita.ai/v3/tagging"


# -------------------------------------------------------------------
# GEMINI CLIENT (fallback)
# -------------------------------------------------------------------

class GeminiVisionClient:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def classify(self, image_bytes: bytes, category="", user_desc=""):
        image = preprocess_image(image_bytes)

        prompt = f"""
        You are tagging a clothing item.
        Category: {category}
        User description: {user_desc}
        Return only a short comma-separated list of tags.
        """

        response = self.model.generate_content([prompt, image])
        tags = [t.strip() for t in (response.text or "").split(",") if t.strip()]
        return {"tags": tags}


# Initialize singleton Gemini client
gemini_client = GeminiVisionClient()

def preprocess_image(image_bytes: bytes) -> bytes:
    """Resize image for API calls."""
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((512, 512))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

# def call_novita_tags(image_bytes: bytes, category_hint: str = "") -> list:
#     """Novita V3 Structured Tagging."""
#     b64_image = base64.b64encode(image_bytes).decode("utf-8")
#     payload = {"image": b64_image, "description": category_hint, "return_type": "tags"}
#     headers = {"Authorization": f"Bearer {Config.NOVITA_API_KEY}", "Content-Type": "application/json"}
    
#     try:
#         resp = requests.post(NOVITA_TAGGING_URL, json=payload, headers=headers, timeout=20)
#         resp.raise_for_status()
#         data = resp.json()
#         return [t["name"].lower() for t in data.get("tags", []) if "name" in t]
#     except Exception as e:
#         print(f"❌ Novita Error: {e}")
#         return []

def call_imagga_safe(image_bytes: bytes):
    """V2 Tagging with JSON crash protection."""
    auth = (Config.IMAGGA_KEY, Config.IMAGGA_SECRET)
    try:
        # Step 1: Upload to Imagga
        up_resp = requests.post("https://api.imagga.com/v2/uploads", 
                                 files={"image": image_bytes}, auth=auth, timeout=10)
        if up_resp.status_code != 200: return []
        
        upload_id = up_resp.json().get("result", {}).get("upload_id")
        
        # Step 2: Get Tags
        tag_resp = requests.get(f"https://api.imagga.com/v2/tags?image_upload_id={upload_id}", 
                                 auth=auth, timeout=10)
        
        # FIX: Check status before calling .json() to avoid 500 error
        if tag_resp.status_code == 200:
            data = tag_resp.json()
            return [t["tag"]["en"].lower() for t in data["result"]["tags"][:5]]
    except Exception as e:
        print(f"⚠️ Imagga skipped: {e}")
    return []

def get_tags(image_bytes, category="", user_desc=""):
    """The Master Pipeline: Logic flow to ensure we always get something."""
    # 1. Try Imagga (Reliable object detection)
    tags = call_imagga_safe(image_bytes)
    if tags: return tags

    # 2. Try BLIP (Great for descriptions)
    caption = call_hf_with_retry_blip(image_bytes)
    if caption:
        return [tag for tag in caption.lower().split() if len(tag) > 3]

    # 3. Gemini Fallback (The 'Smart' backup)
    try:
        res = gemini_client.classify(image_bytes, category, user_desc)
        return res.get("tags", [])
    except:
        return [category or "clothing"]
    
def call_hf_with_retry_blip(image_bytes: bytes):
    """
    Uses HF BLIP image captioning model.
    Returns a caption string or None.
    """

    HF_BLIP_URL = (
        "https://api-inference.huggingface.co/models/"
        "Salesforce/blip-image-captioning-base"
    )

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
        "Connection": "close"
    }

    # Resize + compress image (important for Windows + HF)
    image_bytes = preprocess_image(image_bytes)
    b64_img = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "inputs": b64_img
    }

    for attempt in range(1, MAX_HF_RETRIES + 1):
        try:
            response = requests.post(
                HF_BLIP_URL,
                headers=headers,
                json=payload,
                timeout=(5, 60)
            )
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"]

        except Exception as e:
            print(f"⚠️ BLIP attempt {attempt} failed: {e}")
            if attempt < MAX_HF_RETRIES:
                time.sleep(min(BASE_RETRY_DELAY * attempt, 8))

    return None

# def get_hf_tags_with_fallback(image_bytes, category, user_desc=""):
#     """
#   

#     # -------------------------------------------------------
#     # 1️⃣ Category-specific candidate labels
#     CATEGORY_LABELS = {
#         "tops": ["t-shirt", "shirt", "blouse", "sweater"],
#         "bottoms": ["jeans", "pants", "shorts", "skirt"],
#         "shoes": ["sneakers", "boots", "heels"],
#         "accessories": ["belt", "hat", "scarf"]
#     }

#     candidate_labels = CATEGORY_LABELS.get(
#         category,
#         ["top", "bottom", "shoes", "accessory"]
#     )

#     # -------------------------------------------------------
#     # 2️⃣ HF attempt (retries handled internally)
#     hf_tags = call_hf_with_retry(
#         image_bytes=image_bytes,
#         candidate_labels=candidate_labels
#     )

#     # -------------------------------------------------------
#     # 3️⃣ Gemini fallback if HF failed or empty
#     if hf_tags and len(hf_tags) > 0:
#         print(f"✅ HF tags: {hf_tags}")
#         return hf_tags

#     print("⚠️ HF failed or empty, falling back to Gemini")

#     try:
#         gemini_result = gemini_client.classify(
#             image_bytes=image_bytes,
#             category=category,
#             user_desc=user_desc
#         )
#         print(f"✨ Gemini tags: {gemini_result.get('tags', [])}")
#         return gemini_result.get("tags", [])
#     except Exception as e:
#         print(f"❌ Gemini fallback failed: {e}")
#         return []

def async_tag_update(item_id, image_bytes, category, user_desc=""):
    """
    Background tagging using Novita + Imagga + Gemini.
    Updates Supabase asynchronously.
    """
    top_tags = get_tags(image_bytes, category, user_desc)
    if not top_tags:
        top_tags = ["casual"]

    try:
        supabase.table("wardrobe_items") \
            .update({"tags": top_tags, "tag_status": "completed"}) \
            .eq("id", item_id).execute()
        print(f"✅ Updated item {item_id} with tags: {top_tags}")
    except Exception as e:
        print(f"❌ Failed async tag update for {item_id}: {e}")
        supabase.table("wardrobe_items") \
            .update({"tag_status": "failed"}).eq("id", item_id).execute()

# --------------------------
# ROUTES
# --------------------------
@wardrobe_bp.route("/items", methods=["POST"])
def create_wardrobe_item():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"error": "unauthorized"}), 401

    file = request.files.get("file")
    category = request.form.get("category", "top")
    description = request.form.get("description", "")
    
    if not file: return jsonify({"error": "No file"}), 400

    file_bytes = file.read()

    # 1. Deduplicate & Upload (Saves space immediately)
    uploaded_path = upload_image(user_id, file_bytes, file.filename)
    if not uploaded_path:
        return jsonify({"error": "Failed to upload image"}), 500

    # 2. Get Tags (Master Pipeline handles all fallbacks)
    tags = get_tags(file_bytes, category, description)

    try:
        # 3. Save to DB
        rpc_params = {
            "p_user_id": user_id,
            "p_image_url": uploaded_path,
            "p_category": category,
            "p_tags": tags
        }
        new_item = call_rpc("create_wardrobe_item", rpc_params)
        return jsonify({"item": new_item, "tag": tags[0] if tags else category}), 201

    except Exception as e:
        print(f"🔥 Database Error: {e}")
        return jsonify({"error": "Database entry failed"}), 500

@wardrobe_bp.route("/items", methods=["GET"])
def get_wardrobe():
    """
    Get all wardrobe items for the current user.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    items = call_rpc("get_user_wardrobe", {"p_user_id": user_id})
    if items is None:
        return jsonify({"items": [], "debug_msg": "no data"}), 200

    return jsonify({"items": items}), 200

@wardrobe_bp.route("/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    """
    Delete a wardrobe item and remove its image from storage.
    """
    user_id = get_current_user_id()
    try:
        item = supabase.table("wardrobe_items").select("image_url").eq("id", item_id).single().execute()
        if item.data:
            path = item.data["image_url"]
            supabase.storage.from_("wardrobe-images").remove([path])
            supabase.table("wardrobe_items").delete().eq("id", item_id).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"items": items}), 200
@wardrobe_bp.route("/items/<item_id>", methods=["GET"])
def get_wardrobe_item(item_id):
    """
    Get single wardrobe item by ID for current user.
    """
    user_id = get_current_user_id()
    if not user_id: return jsonify({"error": "unauthorized"}), 401

    res = supabase.table("wardrobe_items").select("*") \
        .eq("id", item_id).eq("user_id", user_id).single().execute()

    if not res.data: return jsonify({"error": "Item not found"}), 404
    return jsonify({"item": res.data}), 200

@wardrobe_bp.route("/simple-ootd", methods=["GET"])
def get_simple_ootd():
    """
    Random OOTD: top + bottom + shoes for current user.
    """
    user_id = get_current_user_id()
    if not user_id: return jsonify({"error": "unauthorized"}), 401

    res = supabase.table("wardrobe_items").select("*").eq("user_id", user_id).execute()
    items = res.data or []

    tops    = [i for i in items if i["category"]=="top"]
    bottoms = [i for i in items if i["category"]=="bottom"]
    shoes   = [i for i in items if i["category"]=="shoes"]
    sel = []
    if tops: sel.append(random.choice(tops))
    if bottoms: sel.append(random.choice(bottoms))
    if shoes: sel.append(random.choice(shoes))

    ootd = [
        {
            "id": i["id"],
            "type": i["category"],
            "image_url": i["image_url"],
            "color": i.get("color", "Neutral")
        } for i in sel
    ]
    return jsonify(ootd)

def repair_null_tags():
    """
    Repairs wardrobe items that have missing or failed tags.
    Triggered from frontend "Repair Tags" button.
    """

    # Import here to avoid circular imports
    from your_db_module import (
        get_items_with_missing_tags,
        update_item_tags,
        mark_item_failed  # optional but recommended
    )

    items = get_items_with_missing_tags()
    repaired_count = 0

    for item in items:
        try:
            image_path = f"./uploads/{item['image_url']}"

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # -------------------------------------------------------
            # 1️⃣ TRY HUGGING FACE (WITH RETRIES)
            # -------------------------------------------------------

            tags = call_hf_with_retry(image_bytes)

            # -------------------------------------------------------
            # 2️⃣ FALLBACK TO GEMINI (ONLY IF HF FAILED OR EMPTY)
            # -------------------------------------------------------

            # ✅ FIX #5: Empty list ≠ success
            if tags is None or len(tags) == 0:
                try:
                    gemini_result = gemini_client.classify(image_bytes)
                    tags = gemini_result.get("tags", [])
                except Exception as gem_err:
                    print(f"❌ Gemini fallback failed for item {item['id']}: {gem_err}")
                    tags = None

            # -------------------------------------------------------
            # 3️⃣ UPDATE DATABASE
            # -------------------------------------------------------

            if tags and len(tags) > 0:
                update_item_tags(item["id"], tags)
                repaired_count += 1
            else:
                # Optional but HIGHLY recommended
                mark_item_failed(item["id"])

        except Exception as item_err:
            # ✅ FIX #6: Item-level isolation
            # One bad image never breaks the batch
            print(f"❌ Failed processing item {item['id']}: {item_err}")
            mark_item_failed(item["id"])

    return jsonify({
        "repaired": repaired_count,
        "attempted": len(items)
    })

    # Optionally, wait for threads to finish
    for t in threads:
        t.join()
        repaired_count += 1

    estimated_cost_usd = round(repaired_count * 0.02, 2)  # ~2 cents per HF request

    return jsonify({
        "msg": f"Attempting to repair {repaired_count} items using HF + Gemini fallback",
        "estimated_cost_usd": estimated_cost_usd
    }), 200


@wardrobe_bp.route("/items/favorite", methods=["POST"])
def toggle_favorite():
    """
    Toggle favorite status for an item.
    """
    user_id = get_current_user_id()
    if not user_id: return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    item_id = data.get("item_id")
    is_favorite = data.get("is_favorite", False)
    if not item_id: return jsonify({"error": "Missing item_id"}), 400

    try:
        supabase.table("wardrobe_items") \
            .update({"is_favorite": is_favorite}) \
            .eq("id", item_id).eq("user_id", user_id).execute()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@wardrobe_bp.route("/insights/colors", methods=["GET"])
def get_color_insights():
    """
    Get color distribution insights for current user.
    """
    user_id = get_current_user_id()
    if not user_id: return jsonify({"error": "unauthorized"}), 401

    res = supabase.rpc("get_color_distribution", {"p_user_id": user_id}).execute()
    return jsonify(res.data)
print("HF URL USED 👉", HF_CLIP_URL)
print("Gemini model 👉", gemini_client.model._model_name)
