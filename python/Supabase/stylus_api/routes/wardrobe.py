# backend/stylus_api/routes/wardrobe.py
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc, upload_image
from storage3.exceptions import StorageApiError
from .profile import supabase
import google.generativeai as genai
import json, random, time, threading, requests, base64
from ..config import Config
import PIL.Image
from io import BytesIO

from concurrent.futures import ThreadPoolExecutor, as_completed
IMAGGA_DISABLED = False
wardrobe_bp = Blueprint("wardrobe", __name__)

# AI MODELS CONFIGURATION
# ===========================

# ---- Gemini Vision (expensive but good quality) ----
genai.configure(api_key=Config.GEM)
vision_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# ---- Hugging Face Fallback ----
HF_API_KEY = Config.HUGGING_FACE

# Hugging Face CLIP Zero-Shot Classificatio
HF_CLIP_URL = "https://router.huggingface.co/hf-inference/models/openai/clip-vit-base-patch32"

HF_HEADERS = {"Authorization": f"Bearer {Config.HUGGING_FACE}"}

# --- Fashion keywords for filtering Imagga tags ---
FASHION_KEYWORDS = {
    # ---- Core Clothing Types ----
    "hoodie", "sweater", "shirt", "t-shirt", "jeans", "skirt", "shorts",
    "jacket", "coat", "blazer", "dress", "pants", "trousers",
    "sweatpants", "cargo", "vest",

    # ---- Materials / Textures ----
    "denim", "leather", "wool", "silk", "cotton", "knit",
    "corduroy", "linen", "velvet",

    # ---- Styles / Details ----
    "vintage", "oversized", "slim", "graphic", "striped", "plaid",
    "minimalist", "streetwear", "casual", "formal", "sportswear",
    "sleeveless", "long-sleeved", "buttoned",

    # ---- Shoes & Accessories ----
    "sneakers", "boots", "loafers", "sandals",
    "beanie", "cap", "belt", "watch", "backpack",

    # ---- University / Corporate ----
    "tie", "suit", "oxford", "dress-shirt", "slacks",
    "chinos", "cardigan", "turtleneck", "leather-shoes",

    # ---- Student Casual ----
    "varsity-jacket", "tote-bag"
}
COLORS_LIST = {
    "black", "white", "grey", "gray", "navy", "blue", "red", "green", 
    "yellow", "brown", "beige", "cream", "pink", "purple", "orange", "maroon"
}
# Predefined student wardrobe labels
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
IMAGGA_V3_DISABLED = False

# -------------------------------------------------------------------
# GEMINI CLIENT (fallback)
# -------------------------------------------------------------------

def preprocess_image(image_bytes: bytes) -> bytes:
    """Resize and compress images before sending to AI APIs."""
    img = PIL.Image.open(BytesIO(image_bytes)).convert("RGB")
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

def call_gemini(file_bytes, category_hint, user_desc=""):
    """
    Gemini Vision fallback.
    Used only when Imagga fails or returns weak tags.
    """
    try:
        print(f"✨ Tier 3: Gemini Vision for '{category_hint}'")

        img = PIL.Image.open(BytesIO(file_bytes))

        prompt = f"""
        Analyze this {category_hint} for a university student wardrobe.

        User notes: {user_desc}

        Focus on professional or student-appropriate items
        such as ties, blazers, oxford shirts, loafers, hoodies,
        varsity jackets, or sneakers.

        Allowed vocabulary:
        {", ".join(sorted(FASHION_KEYWORDS))}

        Return ONLY a comma-separated list of 3–5 keywords.
        """

        response = vision_model.generate_content([prompt, img])
        if response and response.text:
            tags = [t.strip().lower() for t in response.text.split(",") if t.strip()]
            return tags if tags else None

    except Exception as e:
        print(f"❌ Gemini Vision failed: {e}")

    return None
def get_ultimate_tags(public_url, file_bytes, category_hint, user_desc=""):
    """
    Tiered Tagging Pipeline:
    1️⃣ Imagga V3 (Tags + Colors)
    2️⃣ Imagga V2 (Tags + Colors)
    3️⃣ Gemini Vision (fallback)
    4️⃣ Emergency Default
    """
    global IMAGGA_DISABLED, IMAGGA_V3_DISABLED
    auth = (Config.IMAGGA_KEY, Config.IMAGGA_SECRET)

    all_tags = []

    # -----------------------------
    # Attempt Imagga V3 (primary)
    # -----------------------------
    if not IMAGGA_DISABLED and not IMAGGA_V3_DISABLED:
        try:
            print(f"📡 Tier 1: Attempting Imagga V3 Tags + Colors")

            # V3 tags + caption
            resp_tags = requests.get(
                "https://api.imagga.com/v3/tags",
                auth=auth,
                params={
                    "image_url": public_url,
                    "threshold": 20,
                    "model": "pro",
                    "include_caption": "true"
                },
                timeout=10
            )

            # V3 color via v2 endpoint (stable)
            resp_colors = requests.get(
                "https://api.imagga.com/v2/colors",
                auth=auth,
                params={"image_url": public_url},
                timeout=10
            )

            raw_tags = []
            if resp_tags.status_code == 200:
                data = resp_tags.json().get("result", {})
                raw_tags = [t["tag"]["en"].lower() for t in data.get("tags", [])]
                caption = data.get("caption", {}).get("en", "")
                if caption:
                    raw_tags.extend(caption.lower().split())

            color_tags = []
            if resp_colors.status_code == 200:
                color_data = resp_colors.json().get("result", {}).get("colors", {}).get("image_colors", [])
                if color_data:
                    color_tags.append(color_data[0]["closest_palette_color"].lower())

            all_tags = raw_tags + color_tags
            print(f"📌 Imagga V3 tags: {raw_tags}")
            print(f"📌 Imagga V3 colors: {color_tags}")

            if all_tags:
                return list(set(all_tags))

        except Exception as e:
            print(f"⚠️ Imagga V3 failed: {e}")

    # -----------------------------
    # Attempt Imagga V2 (secondary)
    # -----------------------------
    if not IMAGGA_DISABLED:
        try:
            print(f"📡 Tier 2: Attempting Imagga V2 Tags + Colors")

            resp_tags_v2 = requests.get(
                "https://api.imagga.com/v2/tags",
                auth=auth,
                params={"image_url": public_url, "threshold": 20},
                timeout=10
            )
            resp_colors_v2 = requests.get(
                "https://api.imagga.com/v2/colors",
                auth=auth,
                params={"image_url": public_url},
                timeout=10
            )

            raw_tags_v2 = []
            if resp_tags_v2.status_code == 200:
                raw_tags_v2 = [t["tag"]["en"].lower() for t in resp_tags_v2.json().get("result", {}).get("tags", [])]

            color_tags_v2 = []
            if resp_colors_v2.status_code == 200:
                color_data = resp_colors_v2.json().get("result", {}).get("colors", {}).get("image_colors", [])
                if color_data:
                    color_tags_v2.append(color_data[0]["closest_palette_color"].lower())

            all_tags = raw_tags_v2 + color_tags_v2
            print(f"📌 Imagga V2 tags: {raw_tags_v2}")
            print(f"📌 Imagga V2 colors: {color_tags_v2}")

            if all_tags:
                return list(set(all_tags))

            # If V2 returned 403: disable further Imagga
            if resp_tags_v2.status_code == 403 or resp_colors_v2.status_code == 403:
                IMAGGA_DISABLED = True
                print("🚫 Imagga rate limit - disabling Imagga")

        except Exception as e:
            print(f"⚠️ Imagga V2 failed: {e}")

    # -----------------------------
    # Tier 3: Gemini Vision
    # -----------------------------
    try:
        print("✨ Tier 3: Falling back to Gemini Vision")
        # Use a valid vision model
        vision_model = genai.GenerativeModel("gemini-1.5")
        prompt = f"""
Analyze this image for wardrobe tags.
Category hint: {category_hint}
User notes: {user_desc}
Return a comma-separated list of clothing-related keywords and color hints.
Allowed keywords: {', '.join(sorted(FASHION_KEYWORDS))}
"""
        response = vision_model.generate_content([prompt, PIL.Image.open(BytesIO(file_bytes))])
        if response and response.text:
            gemini_tags = [t.strip().lower() for t in response.text.split(",") if t.strip()]
            print(f"📌 Gemini Vision tags: {gemini_tags}")
            return gemini_tags
    except Exception as e:
        print(f"❌ Gemini Vision failed: {e}")

    # -----------------------------
    # Tier 4: Emergency Default
    # -----------------------------
    default = [category_hint, "clothing"]
    print(f"⚠️ All tiers failed; returning default tags: {default}")
    return default


# -------------------------------------------------------------------
# ASYNC TAG UPDATE
# -------------------------------------------------------------------
def async_tag_update(item_id, public_url, file_bytes, category, user_desc=""):
    """
    Background tagging using the ultimate tagging pipeline.
    Updates Supabase asynchronously.
    """
    try:
        top_tags = get_ultimate_tags(public_url, file_bytes, category, user_desc)
        if not top_tags:
            top_tags = ["casual"]

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
    Upload a wardrobe item and auto-generate tags using the tiered pipeline:
    1️⃣ Imagga V2 (cheap)
    2️⃣ Imagga V3 (more accurate)
    3️⃣ Gemini Vision (fallback)
    4️⃣ Emergency default
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    file = request.files.get("file")
    category = request.form.get("category", "top")
    description = request.form.get("description", "")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    file_bytes = file.read()

    try:
        # -----------------------------
        # Step 1: Upload to Supabase Storage
        # -----------------------------
        storage_path = upload_image(user_id, file_bytes, file.filename)
        base_url = current_app.config["SUPABASE_URL"].rstrip('/')
        public_url = f"{base_url}/storage/v1/object/public/wardrobe-images/{storage_path}"

        # -----------------------------
        # Step 2: Get tags using tiered pipeline
        # -----------------------------
        tags = get_ultimate_tags(
            public_url=public_url,
            file_bytes=file_bytes,  # Needed only for Gemini fallback
            category_hint=category,
            user_desc=description
        )

        # -----------------------------
        # Step 3: Insert into DB via RPC
        # -----------------------------
        rpc_params = {
            "p_user_id": user_id,
            "p_image_url": storage_path,
            "p_category": category,
            "p_tags": tags
        }
        new_item = call_rpc("create_wardrobe_item", rpc_params)

        # -----------------------------
        # Step 4: Return success response
        # -----------------------------
        return jsonify({"item": new_item, "tags": tags}), 201

    except Exception as e:
        print(f"❌ Error creating wardrobe item: {e}")
        return jsonify({"error": str(e)}), 500


@wardrobe_bp.route("/items", methods=["GET"])
def get_wardrobe():
    """
    Retrieve all wardrobe items for the current user.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    items = call_rpc("get_user_wardrobe", {"p_user_id": user_id})
    return jsonify({"items": items or []}), 200

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

@wardrobe_bp.route("/repair-null-tags", methods=["POST"])
def repair_null_tags():
    """
    Repair wardrobe items that have null or incomplete tags.
    
    Uses a tiered AI pipeline:
    1️⃣ Imagga V2 (cheap, fast)
    2️⃣ Imagga V3 (more accurate)
    3️⃣ Gemini Vision (expensive fallback)
    4️⃣ Emergency default
    
    Stops at the first successful tier to save API costs.

    Returns:
        JSON with the count of repaired items.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    try:
        # Only retry FAILED items (not pending / completed)
        res = supabase.table("wardrobe_items") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("tag_status", "failed") \
            .execute()

        items = res.data or []
        repaired = 0
        base_url = current_app.config["SUPABASE_URL"].rstrip("/")

        for item in items:
            public_url = f"{base_url}/storage/v1/object/public/wardrobe-images/{item['image_url']}"

            img_resp = requests.get(public_url, timeout=10)
            if img_resp.status_code != 200:
                continue

            tags = get_ultimate_tags(
                public_url,
                img_resp.content,
                item["category"],
                item.get("description", "")
            )

            # CRITICAL VALIDATION:
            # If tags are only fallback-level, keep status FAILED
            is_real_success = (
                tags
                and not (len(tags) == 2 and "clothing" in tags)
            )

            new_status = "completed" if is_real_success else "failed"

            rpc_payload = {
                "p_item_id": str(item["id"]),
                "p_tags": list(tags),
                "p_status": str(new_status)
            }

            call_rpc("update_wardrobe_item_status", rpc_payload)

            if is_real_success:
                repaired += 1

        return jsonify({"repaired": repaired}), 200

    except Exception as e:
        print(f"🔥 Repair failed: {e}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"🔥 Repair failure: {e}")
        return jsonify({"error": "Repair failed", "details": str(e)}), 500

@wardrobe_bp.route("/items/<item_id>/repair-tags", methods=["POST"])
def repair_tags(item_id):
    try:
        # Fetch item
        item = supabase.table("wardrobe_items").select("*").eq("id", item_id).single().execute().data
        if not item:
            return jsonify({"error": "Item not found"}), 404

        # Mark as repairing
        supabase.table("wardrobe_items").update({"tag_status": "repairing"}).eq("id", item_id).execute()

        # Kick off background repair (could be via Celery / threading / async task)
        from threading import Thread
        Thread(target=async_tag_update, args=(item_id, item["image_bytes"], item["category"], item.get("description",""))).start()

        return jsonify({"message": "Repair started", "tag_status": "repairing"}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
# print("HF URL USED 👉", HF_CLIP_URL)
# print("Gemini model 👉", gemini_client.model._model_name)

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
