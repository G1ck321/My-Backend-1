# backend/stylus_api/routes/wardrobe.py
from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc, upload_image
from storage3.exceptions import StorageApiError
from .profile import supabase
import google.generativeai as genai
import json
import random
import time
import threading
import requests
from ..config import Config
import base64
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
# HF_CLIP_URL = "https://router.huggingface.co/hf-inference/pipeline/zero-shot-image-classification"
# HF_CLIP_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
HF_API_KEY = Config.HUGGING_FACE

# Hugging Face CLIP Zero-Shot Classification
# This model compares an image against a list of text labels you provide.
# HF_CLIP_URL = "https://router.huggingface.co/models/sentence-transformers/clip-ViT-B-32"
HF_CLIP_URL = (
    "https://api-inference.huggingface.co/pipeline/zero-shot-image-classification"
)

# HF_HEADERS = {"Authorization": f"Bearer {Config.HUGGING_FACE}"}

# HF_CLIP_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
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


# -------------------------------------------------------------------
# GEMINI CLIENT (fallback)
# -------------------------------------------------------------------

class GeminiVisionClient:
    """
    Replace this with your real Gemini Vision SDK.
    Important: Vision models DO NOT use `.generate()`.
    They use `.classify()` / `.predict()` depending on SDK.
    """

    def classify(self, image_bytes: bytes) -> dict:
        # TODO: Replace with real Gemini Vision API call
        return {
            "tags": ["top", "casual"]
        }


gemini_client = GeminiVisionClient()


def call_hf_with_retry(image_bytes: bytes, candidate_labels: list[str]):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    for attempt in range(1, MAX_HF_RETRIES + 1):
        try:
            response = requests.post(
                HF_URL,
                headers=headers,
                files={"file": image_bytes},
                data={
                    "candidate_labels": json.dumps(candidate_labels)
                },
                timeout=20
            )
            response.raise_for_status()

            labels = response.json().get("labels")
            if isinstance(labels, list):
                return labels

        except Exception as e:
            print(f"⚠️ HF attempt {attempt} failed: {e}")
            if attempt < MAX_HF_RETRIES:
                time.sleep(min(BASE_RETRY_DELAY * attempt, 8))

    return None

def get_hf_tags_with_fallback(image_bytes, category, user_desc=""):
    """
    High-level tag generator.
    - Tries HF with retries
    - Falls back to Gemini if HF fails
    - Applies category + user context
    """

    # -------------------------------------------------------
    # 1️⃣ Category-specific candidate labels
    # -------------------------------------------------------

    CATEGORY_LABELS = {
        "tops": ["t-shirt", "shirt", "blouse", "sweater"],
        "bottoms": ["jeans", "pants", "shorts", "skirt"],
        "shoes": ["sneakers", "boots", "heels"],
        "accessories": ["belt", "hat", "scarf"]
    }

    candidate_labels = CATEGORY_LABELS.get(
        category,
        ["top", "bottom", "shoes", "accessory"]
    )

    # -------------------------------------------------------
    # 2️⃣ HF attempt (retries handled internally)
    # -------------------------------------------------------

    hf_tags = call_hf_with_retry(
        image_bytes=image_bytes,
        candidate_labels=candidate_labels
    )

    # -------------------------------------------------------
    # 3️⃣ Gemini fallback if HF failed or empty
    # -------------------------------------------------------

    if hf_tags is None or len(hf_tags) == 0:
        try:
            gemini_result = gemini_client.classify(
                image_bytes=image_bytes,
                category=category,
                user_desc=user_desc
            )
            return gemini_result.get("tags", [])
        except Exception as e:
            print(f"❌ Gemini fallback failed: {e}")
            return []

    return hf_tags



def async_hf_tag_update(item_id, image_bytes, category, user_desc=""):
    """
    Background thread: tag an image using HF CLIP, fall back to Gemini if needed,
    then update the Supabase record. Never blocks uploads.
    """
    top_tags = get_hf_tags_with_fallback(image_bytes, category, user_desc)
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
    """
    Upload wardrobe item with image, tag using HF CLIP (fallback to Gemini), store in Supabase.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    file = request.files.get("file")
    category = request.form.get("category", "top")
    description = request.form.get("description", "")

    if not file:
        return jsonify({"error": "No file"}), 400

    file_bytes = file.read()

    # --------------------------
    # Step 1: Initial tagging (HF + Gemini fallback)
    # --------------------------
    tags = get_hf_tags_with_fallback(file_bytes, category, description)
    primary_tag = tags[0] if tags else "casual"

    try:
        # --------------------------
        # Step 2: Upload image to storage
        # --------------------------
        uploaded_path = upload_image(user_id, file_bytes, file.filename)

        # --------------------------
        # Step 3: Insert item into Supabase DB
        # --------------------------
        rpc_params = {
            "p_user_id": user_id,
            "p_image_url": uploaded_path,
            "p_category": category,
            "p_tags": tags
        }
        new_item = call_rpc("create_wardrobe_item", rpc_params)

        # --------------------------
        # Step 4: Background refinement (safe, non-blocking)
        # --------------------------
        threading.Thread(
            target=async_hf_tag_update,
            args=(new_item["id"], file_bytes, category, description),
            daemon=True
        ).start()

        return jsonify({"item": new_item, "tag": primary_tag}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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