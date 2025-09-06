import os
from flask import Flask, render_template
import requests
from twilio.rest import Client

app = Flask(__name__)

# Optional Unsplash key; if absent we skip API calls.
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")  # Unsplash requires Authorization: Client-ID <key>
# Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
twilio_client = Client("ACe3f34e847ee786230a7f279a9d29373f","856be243f6ef926ac7a02c7e7949b1dd")

# Curated shoe images (direct CDN links) – safe, no API key required
CURATED_IMAGES = [
    # Urban Runner
    "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=900&q=80",
    # Classic Leather
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=80",
    # Elegant Heels
    "https://images.unsplash.com/photo-1491553895911-0055eca6402d?auto=format&fit=crop&w=900&q=80",
    # Street Sneaker
    "https://images.unsplash.com/photo-1454023492550-5696f8ff10e1?auto=format&fit=crop&w=900&q=80",
    # Mountain Hiker
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=900&q=80",
    # Eco Slip-On
    "https://images.unsplash.com/photo-1491553895911-0055eca6402d?auto=format&fit=crop&w=900&q=80",
    # Night Jogger
    "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=900&q=80",
]

PRODUCT_NAMES = [
    "Urban Runner",
    "Classic Leather",
    "Elegant Heels",
    "Street Sneaker",
    "Mountain Hiker",
    "Eco Slip-On",
    "Night Jogger",
]

def fetch_unsplash_photos(count=6):
    """Fetch extra shoe photos when an Unsplash key is present; otherwise return []"""
    if not UNSPLASH_ACCESS_KEY:
        return []
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {"query": "shoes", "per_page": count, "orientation": "portrait"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    if not r.ok:
        return []
    data = r.json()
    return [item["urls"]["regular"] for item in data.get("results", [])]

def build_products():
    """Combine curated and optional Unsplash photos and generate prices."""
    images = CURATED_IMAGES.copy()
    images += fetch_unsplash_photos(max(0, len(PRODUCT_NAMES) - len(images)))
    images = (images + CURATED_IMAGES)[:len(PRODUCT_NAMES)]
    products = []
    for idx, name in enumerate(PRODUCT_NAMES):
        price = 49 + 15 * idx  # base $49, +$15 step per index
        products.append({"name": name, "img": images[idx], "price": f"${price:.2f}"})
    return products

@app.route("/")
def index():
    products = build_products()
    return render_template("index.html", products=products)

def safe_format_date(dt):
    """Return a human readable datetime string from Twilio's date_sent, handling None or str."""
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        return dt
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt)

def fetch_twilio_balance():
    """Try SDK balance first; fall back to REST Balance endpoint; else 'Unavailable'."""
    # SDK method (available in current twilio-python)
    try:
        data = twilio_client.api.v2010.balance.fetch()
        return f"{float(data.balance):.2f} {data.currency}"
    except Exception:
        pass
    # REST fallback documented by Twilio Support
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Balance.json"
        r = requests.get(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=15)
        if r.ok:
            j = r.json()
            bal = float(j.get("balance", 0.0))
            cur = j.get("currency", "USD")
            return f"{bal:.2f} {cur}"
    except Exception:
        pass
    return "Unavailable"

@app.route("/dashboard")
def dashboard():
    balance = fetch_twilio_balance()
    msgs = []
    try:
        for m in twilio_client.messages.list(limit=50):
            msgs.append({
                "from": m.from_,
                "to": m.to,
                "body": m.body,
                "status": m.status,
                "date_sent": safe_format_date(m.date_sent),
            })
    except Exception:
        msgs = []
    return render_template("dashboard.html", balance=balance, messages=msgs)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
