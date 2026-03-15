"""
IMAGGA V3 FASHION IMAGE ANALYSIS API (Flask)
==============================================
Uses Imagga Tagging V3 + Colors API for production-grade image analysis

Installation:
1. pip install flask requests python-dotenv
2. Add to .env:
   IMAGGA_KEY=your_key
   IMAGGA_SECRET=your_secret
3. Run: python app.py

Features:
- Imagga V3 Tagging (better accuracy than V2)
- Imagga Colors API for dominant colors
- Pattern detection (striped, floral, plaid, etc.)
- Confidence filtering (>40% only)
- Max 10 tags, 5 colors
"""

from flask import Blueprint, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
import os

analyze_bp = Blueprint('analyze', __name__, url_prefix='')

IMAGGA_KEY = os.getenv('IMAGGA_KEY')
IMAGGA_SECRET = os.getenv('IMAGGA_SECRET')

# Pattern keywords for detection
PATTERN_KEYWORDS = {
    'striped': ['striped', 'stripe', 'stripes'],
    'plaid': ['plaid', 'checkered pattern', 'tartan'],
    'floral': ['floral', 'flower', 'flowers'],
    'polka dot': ['polka', 'polka dot', 'dots'],
    'checkered': ['checkered', 'checked'],
    'camouflage': ['camouflage', 'camo'],
}

# ==========================================
# STEP 1: Get tags from Imagga V3 Tagging
# ==========================================

def get_imagga_v3_tags(image_url: str) -> list:
    """
    Call Imagga Tagging V3 API
    Returns list of tags with confidence > 40
    """
    try:
        if not IMAGGA_KEY or not IMAGGA_SECRET:
            raise ValueError('Imagga credentials missing')

        # V3 Tagging endpoint
        response = requests.post(
            'https://api.imagga.com/v2/tagging-v3',
            params={'image_url': image_url},
            auth=HTTPBasicAuth(IMAGGA_KEY, IMAGGA_SECRET)
        )

        if response.status_code != 200:
            print(f"❌ Imagga V3 Tagging failed: {response.status_code}")
            return []

        data = response.json()
        tags_data = data.get('result', {}).get('tags', [])

        # Filter tags: confidence > 40%, max 10 tags
        filtered_tags = [
            tag['tag']['en'].lower()
            for tag in tags_data
            if tag.get('confidence', 0) > 40
        ][:10]

        print(f"✅ Imagga V3 returned {len(filtered_tags)} tags: {filtered_tags}")
        return filtered_tags

    except Exception as e:
        print(f"❌ Imagga V3 error: {e}")
        return []


# ==========================================
# STEP 2: Get colors from Imagga Colors API
# ==========================================

def get_imagga_colors(image_url: str) -> list:
    """
    Call Imagga Colors API
    Returns top 5 dominant colors (percent > 5%)
    """
    try:
        if not IMAGGA_KEY or not IMAGGA_SECRET:
            return []

        response = requests.post(
            'https://api.imagga.com/v2/colors',
            params={'image_url': image_url},
            auth=HTTPBasicAuth(IMAGGA_KEY, IMAGGA_SECRET)
        )

        if response.status_code != 200:
            print(f"❌ Imagga Colors failed: {response.status_code}")
            return []

        data = response.json()
        colors_data = data.get('result', {}).get('colors', [])

        # Filter colors: percent > 5%, max 5 colors
        filtered_colors = [
            color['html_code']  # e.g., #FF5733
            for color in colors_data
            if color.get('percent', 0) > 5
        ][:5]

        print(f"✅ Imagga Colors returned {len(filtered_colors)} colors: {filtered_colors}")
        return filtered_colors

    except Exception as e:
        print(f"❌ Imagga Colors error: {e}")
        return []


# ==========================================
# STEP 3: Detect patterns
# ==========================================

def detect_patterns(tags: list) -> list:
    """
    Match tags against pattern keywords
    Returns list of detected patterns
    """
    detected = []

    for pattern, keywords in PATTERN_KEYWORDS.items():
        for tag in tags:
            if any(kw in tag for kw in keywords):
                if pattern not in detected:
                    detected.append(pattern)
                break

    print(f"✅ Patterns detected: {detected}")
    return detected


# ==========================================
# STEP 4: Extract category
# ==========================================

def extract_category(tags: list) -> str:
    """
    Map tags to clothing category
    """
    category_map = {
        'Top': ['shirt', 'tee', 'blouse', 'sweater', 'hoodie', 'jacket', 'blazer', 'top'],
        'Bottom': ['pants', 'jeans', 'skirt', 'shorts', 'leggings', 'trousers'],
        'Shoes': ['shoe', 'boot', 'sneaker', 'heel', 'sandal', 'loafer'],
        'Dress': ['dress', 'gown', 'jumpsuit'],
        'Outerwear': ['coat', 'parka', 'cardigan', 'vest'],
        'Accessory': ['bag', 'hat', 'scarf', 'belt', 'tie'],
    }

    for category, keywords in category_map.items():
        for tag in tags:
            if any(kw in tag for kw in keywords):
                return category

    return 'Other'


# ==========================================
# MAIN ENDPOINT
# ==========================================

@analyze_bp.route("/api/analyze-image", methods=["POST"])
def analyze_image_v3():
    """
    Main endpoint: Analyze fashion image with Imagga V3

    Request:
    {
        "image_url": "https://example.com/image.jpg"
    }

    Response:
    {
        "tags": ["dress", "summer", "fashion"],
        "patterns": ["floral"],
        "colors": ["#FF5733", "#FFFFFF"],
        "category": "Dress",
        "isClothing": true,
        "confidence": 0.85
    }
    """
    try:
        data = request.get_json() or {}
        image_url = data.get('image_url')

        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400

        print(f"\n🔍 Analyzing: {image_url}")

        # Get tags from V3 Tagging API
        tags = get_imagga_v3_tags(image_url)

        if not tags:
            print("❌ No tags returned, returning fallback")
            return jsonify({
                "tags": [],
                "patterns": [],
                "colors": [],
                "category": "Other",
                "isClothing": False,
                "confidence": 0.2
            }), 200

        # Get colors from Colors API
        colors = get_imagga_colors(image_url)

        # Detect patterns
        patterns = detect_patterns(tags)

        # Extract category
        category = extract_category(tags)

        # Check if it's clothing
        is_clothing = category != 'Other'

        response = {
            "tags": tags,
            "patterns": patterns,
            "colors": colors,
            "category": category,
            "isClothing": is_clothing,
            "confidence": 0.85 if is_clothing else 0.3,
            "source": "imagga_v3"
        }

        print(f"✅ Analysis complete: {response}")
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            "error": str(e),
            "tags": [],
            "patterns": [],
            "colors": [],
            "category": "Other",
            "isClothing": False,
            "confidence": 0.0
        }), 500


# Test endpoint
@analyze_bp.route("/api/analyze-image/test", methods=["POST"])
def test_endpoint():
    """
    Test endpoint with sample image
    curl -X POST http://localhost:5000/api/analyze-image/test
    """
    sample_image = "https://images.pexels.com/photos/1055691/pexels-photo-1055691.jpeg"  # Dress

    data = {"image_url": sample_image}
    return analyze_image_v3.__wrapped__(request.__class__.from_json(
        data,
        mimetype='application/json'
    ))
