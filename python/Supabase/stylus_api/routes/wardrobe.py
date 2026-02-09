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
    1️⃣ Imagga V2 (cheap, fast) - uses circuit breaker
    2️⃣ Imagga V3 (medium-cost, higher accuracy)
    3️⃣ Gemini Vision (expensive fallback, context-aware)
    4️⃣ Emergency Default - ensures we never return None
    
    Stops at first successful result to minimize API costs.
    
    Args:
        public_url (str): Publicly accessible image URL
        file_bytes (bytes): Raw image bytes (for Gemini)
        category_hint (str): Clothing category hint
        user_desc (str): Optional user description/context
    
    Returns:
        List[str]: Tags for the wardrobe item
    """
    global IMAGGA_DISABLED
    auth = (Config.IMAGGA_KEY, Config.IMAGGA_SECRET)

    # -----------------------
    # Tier 1: Imagga V2
    # -----------------------
    if not IMAGGA_DISABLED:
        try:
            print(f"📡 Tier 1: Attempting Imagga V2 for {public_url}")

            resp = requests.get(
                "https://api.imagga.com/v2/tags",
                auth=auth,
                params={"image_url": public_url, "threshold": 20, "language": "en"},
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                raw = [t["tag"]["en"].lower() for t in data.get("result", {}).get("tags", [])]
                tags = [t for t in raw if t in FASHION_KEYWORDS]
                if tags:
                    return tags

            elif resp.status_code == 403:
                IMAGGA_DISABLED = True
                print("🚫 Imagga V2 limit hit — disabling")

        except Exception as e:
            print(f"⚠️ Imagga V2 failed: {e}")

    # -----------------------
    # Tier 2: Imagga V3
    # -----------------------
    if not IMAGGA_DISABLED:
        try:
            print(f"📡 Tier 2: Attempting Imagga V3 for {public_url}")

            resp = requests.get(
                "https://api.imagga.com/v3/tags",
                auth=auth,
                params={
                    "image_url": public_url,
                    "model": "pro",
                    "include_caption": "true"
                },
                timeout=15
            )

            if resp.status_code == 200:
                data = resp.json()
                raw = [t["tag"]["en"].lower() for t in data.get("result", {}).get("tags", [])]

                caption = data.get("result", {}).get("caption", {}).get("en", "")
                if caption:
                    raw.extend(caption.lower().split())

                tags = [t for t in raw if t in FASHION_KEYWORDS]
                if tags:
                    return list(set(tags))

        except Exception as e:
            print(f"⚠️ Imagga V3 failed: {e}")

    # -----------------------
    # Tier 3: Gemini Vision
    # -----------------------
    tags = call_gemini(file_bytes, category_hint, user_desc)
    if tags:
        return tags

    # -----------------------
    # Tier 4: Emergency Safe Fallback
    # -----------------------
    print(f"⚠️ All tagging failed for '{category_hint}' — fallback applied")
    return [str(category_hint), "clothing"]

    # ==========================
    # --- Tier 4: Emergency Default ---
    # ==========================
    print(f"⚠️ All tagging failed; returning default tags for '{category_hint}'")
    return [category_hint, "clothing"]

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
