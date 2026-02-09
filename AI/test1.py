import requests, base64, os
from dotenv import load_dotenv
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests
from io import BytesIO


load_dotenv()
Tok = os.getenv("HUGGING_FACE")

import requests

HF_TOKEN = "YOUR_TOKEN"
HEADERS = {"Authorization": f"Bearer {Tok}"}
MODEL = "openai/clip-vit-large-patch14"  # or Salesforce/blip-image-captioning-base

image_url = "https://wujasfmsjfxnfglbwdti.supabase.co/storage/v1/object/public/wardrobe-images/344fb3b9-f987-4005-bd21-d9ec740700a3/450ea55f-5558-4363-9d17-3e12841339e7_Hippy.jpg"
HF_MODEL = "Salesforce/blip-image-captioning-base"  # Cloud version
payload = {
        "inputs": image_url,  # We can pass the Supabase URL directly
        "options": {"wait_for_model": True}
    }

r = requests.post(f"https://api-inference.huggingface.co/models/{HF_MODEL}",
                      headers=HEADERS,
                      json=payload)

if r.status_code == 200:
    result = r.json()
    # BLIP API returns [{"generated_text": "..."}]
    caption = result[0]["generated_text"]
    print("HF API BLIP Caption:", caption)
else:
    print("HF API request failed:", r.status_code, r.text)