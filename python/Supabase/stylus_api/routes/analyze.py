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

analyze_bp = Blueprint('analyze', __name__, url_prefix='')

# ==========================================
# CONFIGURATION (from environment)
# ==========================================
IMAGGA_KEY = os.getenv('IMAGGA_KEY')
IMAGGA_SECRET = os.getenv('IMAGGA_SECRET')
HF_TOKEN = os.getenv('HUGGING_FACE')
GEM_KEY = os.getenv('GEM')

IMAGGA_DISABLED = not (IMAGGA_KEY and IMAGGA_SECRET)
HF_DISABLED = not HF_TOKEN

# HuggingFace API endpoint
HF_CLIP_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# Fashion keywords for filtering results
FASHION_KEYWORDS = {
    'top', 'shirt', 'blouse', 'tee', 'sweater', 'hoodie', 'cardigan', 'jacket', 'blazer',
    'bottom', 'pants', 'jeans', 'skirt', 'shorts', 'leggings', 'chino', 'khaki',
    'shoe', 'boot', 'sneaker', 'loafer', 'heels', 'sandal', 'pump', 'wearing',
    'casual', 'formal', 'business', 'dress', 'striped', 'solid', 'pattern'
}


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
        # POST to Imagga V2 API with image file
        resp = requests.post(
            "https://api.imagga.com/v2/tags",
            auth=(IMAGGA_KEY, IMAGGA_SECRET),
            files={"image": file_bytes},
            timeout=10
        )

        if resp.status_code != 200:
            print(f"❌ Imagga API error: {resp.status_code}")
            return []

        # Extract tags from response
        tags_data = resp.json().get("result", {}).get("tags", [])

        # Filter for fashion-related keywords only
        fashion_tags = []
        for tag_obj in tags_data[:5]:  # Top 5 tags
            tag_name = tag_obj.get("tag", {}).get("en", "").lower()
            if tag_name and any(keyword in tag_name for keyword in FASHION_KEYWORDS):
                fashion_tags.append(tag_name)

        print(f"✅ Imagga returned {len(fashion_tags)} fashion tags: {fashion_tags}")
        return fashion_tags

    except Exception as e:
        print(f"❌ Imagga API failed: {e}")
        return []


def get_huggingface_tags(file_bytes):
    """
    Call HuggingFace CLIP API as fallback (Tier 2)
    Returns list of fashion-related labels
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
            timeout=10
        )

        if resp.status_code != 200:
            print(f"❌ HuggingFace API error: {resp.status_code}")
            return []

        # HF returns list of classifications
        data = resp.json()
        labels = data.get("labels", []) if isinstance(data, dict) else []

        # Filter for fashion-related keywords
        fashion_labels = []
        for label in labels[:5]:  # Top 5
            if label and any(keyword in label.lower() for keyword in FASHION_KEYWORDS):
                fashion_labels.append(label.lower())

        print(f"✅ HuggingFace returned {len(fashion_labels)} fashion labels: {fashion_labels}")
        return fashion_labels

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
            "category": "Other",  # Would need more complex logic to categorize as Top/Bottom/Shoes
            "color": "Unknown",   # Similar - would need color detection
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
