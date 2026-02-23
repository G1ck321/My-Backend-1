import httpx, os, base64
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)
GEMINI_MODEL_NAME = "models/gemini-2.5-flash"
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

image_path = "https://wujasfmsjfxnfglbwdti.supabase.co/storage/v1/object/public/wardrobe-images/344fb3b9-f987-4005-bd21-d9ec740700a3/pexels-dayong-tien-681073045-18186107.jpg"

image_bytes = httpx.get(image_path).content

resp = model.generate_content([
    "Tell me about this image",
    {
        "mime_type":"image/jpeg",
        "data":image_bytes
    }
])

print(resp.text)