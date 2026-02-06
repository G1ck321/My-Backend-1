from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests

# Load model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Load image
img_url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/green_clothing.jpg"
image = Image.open(requests.get(img_url, stream=True).raw).convert("RGB")

# Generate caption
inputs = processor(image, return_tensors="pt")
out = model.generate(**inputs)
caption = processor.decode(out[0], skip_special_tokens=True)

print("Caption:", caption)
