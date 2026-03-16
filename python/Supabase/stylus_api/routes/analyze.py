"""
FLASK IMPLEMENTATION: Image Analysis Endpoint for Next.js Fallback
===================================================================

This Flask endpoint handles image analysis when Gemini API quota is exhausted.

Installation:
1. Save this file to your Flask backend
2. Add to your main Flask app: from analyze_image import analyze_bp; app.register_blueprint(analyze_bp)
3. Update your .env with: IMAGGA_KEY, IMAGGA_SECRET, HUGGING_FACE, GEM

Location: app/routes/analyze_image.py (or similar in your Flask structure)
"""

from flask import Blueprint, request, jsonify
import base64
import requests
import os
from io import BytesIO
from ..config import Config
analyze_bp = Blueprint('analyze', __name__, url_prefix='')

# ==========================================
# CONFIGURATION (from environment)
# ==========================================
IMAGGA_KEY = Config.IMAGGA_KEY
IMAGGA_SECRET = Config.IMAGGA_SECRET
HF_TOKEN = os.getenv('HUGGING_FACE')
GEM_KEY = os.getenv('GEM')

IMAGGA_DISABLED = not (IMAGGA_KEY and IMAGGA_SECRET)
HF_DISABLED = not HF_TOKEN

# HuggingFace API endpoint - Updated to working model
HF_CLIP_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}" if HF_TOKEN else ""}

# Fashion keywords for filtering results
FASHION_KEYWORDS = {
    'top', 'shirt', 'blouse', 'tee', 'sweater', 'hoodie', 'cardigan', 'jacket', 'blazer',
    'bottom', 'pants', 'jeans', 'skirt', 'shorts', 'leggings', 'chino', 'khaki',
    'shoe', 'boot', 'sneaker', 'loafer', 'heels', 'sandal', 'pump', 'wearing',
    'casual', 'formal', 'business', 'dress', 'striped', 'solid', 'pattern'
}

# Category taxonomy: tag keyword -> display category
CATEGORY_MAP = {
    'Top':    ['shirt', 't-shirt', 'tee', 'blouse', 'top', 'sweater', 'hoodie',
               'cardigan', 'jacket', 'blazer', 'coat', 'polo', 'tank', 'vest'],
    'Bottom': ['pants', 'jeans', 'trousers', 'skirt', 'shorts', 'leggings',
               'chino', 'khaki', 'jogger', 'cargo'],
    'Shoes':  ['shoe', 'shoes', 'boot', 'boots', 'sneaker', 'sneakers', 'loafer',
               'heels', 'sandal', 'sandals', 'pump', 'pumps', 'trainer'],
    'Dress':  ['dress', 'gown', 'jumpsuit', 'romper'],
    'Bag':    ['bag', 'handbag', 'backpack', 'purse', 'tote', 'clutch'],
}

# Color taxonomy: tag keyword -> display color
COLOR_MAP = {
    'Black':  ['black', 'dark', 'ebony', 'charcoal', 'onyx'],
    'White':  ['white', 'ivory', 'cream', 'off-white'],
    'Blue':   ['blue', 'navy', 'cobalt', 'denim', 'indigo', 'azure'],
    'Red':    ['red', 'crimson', 'scarlet', 'maroon', 'burgundy'],
    'Green':  ['green', 'olive', 'khaki', 'lime', 'emerald', 'sage'],
    'Yellow': ['yellow', 'gold', 'mustard', 'amber'],
    'Pink':   ['pink', 'blush', 'rose', 'magenta', 'fuchsia'],
    'Purple': ['purple', 'violet', 'lavender', 'plum'],
    'Brown':  ['brown', 'tan', 'beige', 'camel', 'chocolate', 'nude'],
    'Grey':   ['grey', 'gray', 'silver', 'slate'],
    'Orange': ['orange', 'coral', 'peach', 'rust'],
}


def extract_category(tags: list) -> str:
    """Map Imagga tags to a single display category."""
    for tag in tags:
        tag_lower = tag.lower()
        for category, keywords in CATEGORY_MAP.items():
            if any(kw in tag_lower for kw in keywords):
                return category
    return 'Other'


def extract_color(tags: list) -> str:
    """Map Imagga tags to a single display color."""
    for tag in tags:
        tag_lower = tag.lower()
        for color, keywords in COLOR_MAP.items():
            if any(kw in tag_lower for kw in keywords):
                return color
    return 'Unknown'


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_imagga_tags(file_bytes):
    """
    Call Imagga V2 API only (Tier 1)
    Returns list of fashion-related tags
    """
    if IMAGGA_DISABLED:
        print("⚠️ Imagga disabled - skipping")
        return []

    try:
        # FIX: Create BytesIO object from bytes for proper file upload
        image_file = BytesIO(file_bytes)

        # POST to Imagga V2 API with image file
        resp = requests.post(
            "https://api.imagga.com/v2/tags",
            auth=(IMAGGA_KEY, IMAGGA_SECRET),
            files={"image": ("image.jpg", image_file, "image/jpeg")},  # Proper file format
            timeout=10
        )

        if resp.status_code != 200:
            print(f"❌ Imagga API error: {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")  # Show error details
            return []

        # Extract tags from response
        tags_data = resp.json().get("result", {}).get("tags", [])

        # Filter for fashion-related and color keywords, up to 20 tags
        fashion_tags = []
        all_color_keywords = {kw for keywords in COLOR_MAP.values() for kw in keywords}
        for tag_obj in tags_data[:20]:
            tag_name = tag_obj.get("tag", {}).get("en", "").lower()
            is_fashion = any(keyword in tag_name for keyword in FASHION_KEYWORDS)
            is_color = any(keyword in tag_name for keyword in all_color_keywords)
            if tag_name and (is_fashion or is_color):
                fashion_tags.append(tag_name)

        print(f"✅ Imagga returned {len(fashion_tags)} fashion tags: {fashion_tags}")
        return fashion_tags

    except Exception as e:
        print(f"❌ Imagga API failed: {e}")
        return []


def get_huggingface_tags(file_bytes):
    """
    Call HuggingFace BLIP Image Captioning API as fallback (Tier 2)
    Returns list of fashion-related labels extracted from caption
    """
    if HF_DISABLED:
        print("⚠️ HuggingFace disabled - skipping")
        return []

    try:
        # POST binary image data to HF API
        resp = requests.post(
            HF_CLIP_URL,
            headers=HF_HEADERS,
            data=file_bytes,
            timeout=15  # Increased timeout for model loading
        )

        if resp.status_code != 200:
            print(f"❌ HuggingFace API error: {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return []

        # HF BLIP returns caption like: "a woman wearing a blue striped shirt"
        data = resp.json()

        # Extract caption text
        if isinstance(data, list) and len(data) > 0:
            caption = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            caption = data.get("generated_text", "")
        else:
            caption = ""

        if not caption:
            print("⚠️ HuggingFace returned empty caption")
            return []

        print(f"📝 HuggingFace caption: {caption}")

        # Extract fashion keywords from caption
        caption_lower = caption.lower()
        fashion_labels = []

        # Check for fashion keywords in caption
        all_keywords = set()
        for keywords in CATEGORY_MAP.values():
            all_keywords.update(keywords)

        for keyword in all_keywords:
            if keyword in caption_lower:
                fashion_labels.append(keyword)

        # Also check colors
        all_color_keywords = {kw for keywords in COLOR_MAP.values() for kw in keywords}
        for color_kw in all_color_keywords:
            if color_kw in caption_lower:
                fashion_labels.append(color_kw)

        print(f"✅ HuggingFace returned {len(fashion_labels)} fashion labels: {fashion_labels}")
        return fashion_labels[:10]  # Limit to 10

    except Exception as e:
        print(f"❌ HuggingFace API failed: {e}")
        return []


# ==========================================
# MAIN ENDPOINT: Called by Next.js on Gemini failure
# ==========================================

@analyze_bp.route("/api/analyze-image", methods=["POST"])
def analyze_image_for_tagging():
    """
    NEW ENDPOINT: For Next.js to call when Gemini quota is exhausted

    Request Format:
    {
        "base64Image": "base64_encoded_image_string",
        "mimeType": "image/jpeg"
    }

    Response Format:
    {
        "isClothing": true,
        "category": "Top",
        "color": "Blue",
        "tags": ["casual", "stripe", "blue"],
        "confidence": 0.85,
        "source": "imagga_fallback"
    }
    """
    try:
        # STEP 1: Extract and validate request
        data = request.get_json()
        # FIX: Changed from "image" to "base64Image" (matches Next.js)
        base64_image = data.get("base64Image")
        mime_type = data.get("mimeType", "image/jpeg")

        if not base64_image:
            print("❌ No image provided in request")
            print(f"   Received data keys: {list(data.keys())}")
            return jsonify({"error": "No image provided"}), 400

        print(f"🔍 Analyzing image (mimeType: {mime_type})...")

        # STEP 2: Decode base64 to bytes
        try:
            file_bytes = base64.b64decode(base64_image)
        except Exception as e:
            print(f"❌ Base64 decode error: {e}")
            return jsonify({"error": "Invalid base64 image"}), 400

        # STEP 2.5: Convert WebP to JPEG (Imagga doesn't support WebP)
        if mime_type == 'image/webp':
            try:
                from PIL import Image
                import io

                print("🔄 Converting WebP to JPEG (Imagga requirement)...")

                # Load WebP image
                webp_image = Image.open(io.BytesIO(file_bytes))

                # Convert to RGB (remove alpha channel if present)
                if webp_image.mode in ('RGBA', 'LA', 'P'):
                    rgb_image = Image.new('RGB', webp_image.size, (255, 255, 255))
                    rgb_image.paste(webp_image, mask=webp_image.split()[-1] if webp_image.mode == 'RGBA' else None)
                else:
                    rgb_image = webp_image.convert('RGB')

                # Convert to JPEG bytes
                jpeg_buffer = io.BytesIO()
                rgb_image.save(jpeg_buffer, format='JPEG', quality=90)
                file_bytes = jpeg_buffer.getvalue()

                print("✅ Converted WebP → JPEG successfully")

            except ImportError:
                print("⚠️ PIL/Pillow not installed, cannot convert WebP")
                print("   Install with: pip install Pillow")
                # Continue anyway, let Imagga fail and fall back to HuggingFace
            except Exception as e:
                print(f"⚠️ WebP conversion failed: {e}")
                # Continue anyway, fallback will handle it

        # STEP 3: Try Imagga first (Tier 1)
        tags = get_imagga_tags(file_bytes)

        # STEP 4: If Imagga fails, try HuggingFace (Tier 2)
        if not tags:
            print("📊 Imagga didn't return results, trying HuggingFace...")
            tags = get_huggingface_tags(file_bytes)

        # STEP 5: Last resort - return generic response
        if not tags:
            print("⚠️ Both APIs failed, returning generic response")
            tags = ["clothing", "apparel"]

        # STEP 6: Return structured response
        response = {
            "isClothing": True,
            "category": extract_category(tags),
            "color": extract_color(tags),
            "tags": tags,
            "confidence": 0.5 if tags else 0.3,
            "source": "imagga_fallback"
        }

        print(f"✅ Analysis complete: {len(tags)} tags, confidence: {response['confidence']}")
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Unexpected error in analyze_image: {e}")
        return jsonify({
            "error": str(e),
            "isClothing": True,  # Fallback: assume it's clothing
            "category": "Other",
            "color": "Unknown",
            "tags": [],
            "confidence": 0.2,
            "source": "error_fallback"
        }), 500


# ==========================================
# OPTIONAL: Test endpoint for debugging
# ==========================================

@analyze_bp.route("/api/analyze-image/test", methods=["POST"])
def test_analyze_endpoint():
    """
    Test endpoint - use curl to verify the API is working:

    curl -X POST http://localhost:5000/api/analyze-image/test \
      -H "Content-Type: application/json" \
      -d '{}'

    Should return: {"status": "OK", "imagga": enabled/disabled, "huggingface": enabled/disabled}
    """
    return jsonify({
        "status": "OK",
        "endpoint": "/api/analyze-image",
        "imagga_enabled": not IMAGGA_DISABLED,
        "huggingface_enabled": not HF_DISABLED,
        "message": "Ready to analyze images"
    }), 200
