import requests

# ✅ Replace with your actual Imagga API key & secret
IMAGGA_API_KEY = "acc_f5777de4778a7d5"
IMAGGA_API_SECRET = "eca23db68890e50bef0e5991693f4255"
FASHION_KEYWORDS = set([
    "hoodie", "sweater", "shirt", "t-shirt", "jeans", "skirt",
    "shorts", "jacket", "coat", "shoes", "sneakers", "boots",
    "hat", "cap", "backpack", "bag", "belt", "watch", "scarf",
    'top', 'clothing', 'sleeve'
])

# Test image URL (you can use any public image)
TEST_IMAGE_URL = "https://wujasfmsjfxnfglbwdti.supabase.co/storage/v1/object/public/wardrobe-images/344fb3b9-f987-4005-bd21-d9ec740700a3/pexels-dayong-tien-681073045-18186107.jpg"

def test_imagga_api():
    url = "https://api.imagga.com/v2/tags"
    auth = (IMAGGA_API_KEY, IMAGGA_API_SECRET)
    params = params = {
        "image_url": TEST_IMAGE_URL,
        "language": "en",
        "threshold": 20  # minimum confidence
    }  # only tags >= 20% confidence

    try:
        response = requests.get(url, auth=(IMAGGA_API_KEY, IMAGGA_API_SECRET), params=params)
        response.raise_for_status()
        data = response.json()

        # Extract tags
        tags = [t["tag"]["en"].lower() for t in data.get("result", {}).get("tags", [])]

        # Keep only fashion-relevant tags
        fashion_tags = [t for t in tags if t in FASHION_KEYWORDS]

        print("✅ All tags:", tags)
        print("🎯 Fashion tags:", fashion_tags)

    except Exception as e:
        print("❌ Imagga API call failed:", e)

# Run the test
test_imagga_api()