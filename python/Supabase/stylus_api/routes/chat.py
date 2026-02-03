from flask import Blueprint, request, jsonify
import google.generativeai as genai
import time

from .profile import supabase
from ..routes.context import get_weather
from ..utils.auth import get_current_user_id
from ..config import Config

# ==================================================
# 1. CONFIGURE GEMINI / GEMMA
# ==================================================

genai.configure(api_key=Config.GEM)

# Primary (fast, smart, but quota-limited)
GEMINI_MODEL = "gemini-flash-latest"

# Fallback (cheaper, weaker, more available)
GEMMA_MODEL = "gemma-3-4b-it"

# ==================================================
# 2. BASIC IN-MEMORY RATE LIMIT (PER USER)
# Prevents accidental spam & quota burn
# ==================================================

LAST_CALL = {}

def rate_limit(user_id: str, cooldown: int = 3) -> bool:
    """
    Allows 1 request per user every `cooldown` seconds.
    Returns True if allowed, False if blocked.
    """
    now = time.time()
    last = LAST_CALL.get(user_id, 0)

    if now - last < cooldown:
        return False

    LAST_CALL[user_id] = now
    return True

# ==================================================
# 3. AI GENERATION WITH FALLBACK LOGIC
# ==================================================

def generate_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Attempts Gemini first.
    Falls back to Gemma ONLY on quota / rate limit errors.

    Returns:
        (reply_text, model_used)
    """

    try:
        # --- Try Gemini first ---
        gemini = genai.GenerativeModel(GEMINI_MODEL)
        response = gemini.generate_content(prompt)

        return response.text, GEMINI_MODEL

    except Exception as e:
        error_msg = str(e).lower()

        # --- Detect quota / rate limit errors ---
        quota_errors = ["429", "quota", "rate", "exceeded", "resource_exhausted"]

        if any(err in error_msg for err in quota_errors):
            print("⚠️ Gemini quota hit. Falling back to Gemma.")

            # --- Use Gemma as fallback ---
            gemma = genai.GenerativeModel(GEMMA_MODEL)

            # Gemma works better with shorter prompts
            shortened_prompt = prompt[:2000]

            response = gemma.generate_content(shortened_prompt)
            return response.text, GEMMA_MODEL

        # --- Unknown error: re-raise ---
        raise

# ==================================================
# 4. FLASK BLUEPRINT
# ==================================================

chat_bp = Blueprint("chat", __name__)

# ==================================================
# 5. CHAT ENDPOINT
# ==================================================

@chat_bp.route("/chat-message", methods=["POST"])
def chat():
    try:
        # ------------------------------------------
        # A. AUTHENTICATION
        # ------------------------------------------
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"reply": "Unauthorized"}), 401

        # ------------------------------------------
        # B. RATE LIMIT CHECK
        # ------------------------------------------
        if not rate_limit(user_id):
            return jsonify({
                "reply": "Hold on 😅 Give me a second before asking again."
            }), 429

        # ------------------------------------------
        # C. USER MESSAGE
        # ------------------------------------------
        data = request.get_json()
        user_query = data.get("message", "").strip()

        if not user_query:
            return jsonify({"reply": "Say something first 🙂"}), 400

        # ------------------------------------------
        # D. WEATHER CONTEXT
        # ------------------------------------------
        weather_res = get_weather().get_json()
        temp = weather_res.get("temp", 25)
        cond = weather_res.get("condition", "Clear")

        # ------------------------------------------
        # E. USER WARDROBE CONTEXT
        # ------------------------------------------
        wardrobe_res = (
            supabase
            .table("wardrobe_items")
            .select("category, color, weight, tags") # Fetch more columns!
            .eq("user_id", user_id)
            .execute()
        )

        # Create a more descriptive list
        items_descriptions = []
        for item in wardrobe_res.data:
            desc = f"{item['category']}"
            if item.get('color') and item['color'] != 'unknown':
                desc += f" in {item['color']}"
            if item.get('weight'):
                desc += f" (suitable for {item['weight']} weather)"
            items_descriptions.append(desc)

        # --- F. SYSTEM PROMPT (More Directive) ---
        system_prompt = f"""
You are StyluS, a personal stylist. 
Weather: {temp}°C, {cond}.

Closet Inventory:
{chr(10).join(items_descriptions) if items_descriptions else "The closet is currently empty."}

User's Request: "{user_query}"

Rules:
1. Suggest a specific outfit using ONLY the items listed above.
2. If the user asks for a recommendation, explain WHY it fits the {temp}°C weather.
3. If the wardrobe is empty, tell the user to upload photos of their clothes first.
4. DO NOT ask the user for colors or styles; use the inventory provided.
"""

        # ------------------------------------------
        # G. AI GENERATION (WITH FALLBACK)
        # ------------------------------------------
        reply, model_used = generate_with_fallback(system_prompt)

        # ------------------------------------------
        # H. RESPONSE
        # ------------------------------------------
        return jsonify({
            "reply": reply,
            "model": model_used,
            "weather": {
                "temp": temp,
                "condition": cond
            }
        })

    except Exception as e:
        print("🔥 Chat Error:", str(e))
        return jsonify({
            "reply": "I'm having a fashion brain freeze 😵 Try again shortly."
        }), 500
