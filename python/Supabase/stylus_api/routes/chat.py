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
        profile_res = supabase.table("profiles").select("style_vibe").eq("id", user_id).maybe_single().execute()

        # B. Improved extraction logic
        if profile_res.data and profile_res.data.get("style_vibe"):
            vibe = profile_res.data["style_vibe"]
        else:
            vibe = "Versatile" # Better fallback than "None"

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
            if item.get('tags'):
                desc += f" (Style: {', '.join(item['tags'])})"
            items_descriptions.append(desc)

        # --- F. SYSTEM PROMPT (More Directive) ---
        system_prompt = f"""
You are StyluS, a high-end fashion concierge. 
Style Vibe: {vibe}
Weather: {temp}°C, {cond}.

Inventory:
{chr(10).join(items_descriptions)}

Rules:
1. Suggest an outfit that fits the "{vibe}" aesthetic.
2. Suggest a specific outfit using ONLY the items listed above.
3. If the user asks for a recommendation, explain WHY it fits the {temp}°C weather.
4. If the wardrobe is empty, tell the user to upload photos of their clothes first.
5. DO NOT ask the user for colors or styles; use the inventory provided.
6. NEVER say "one of your items."
7. If the user asks "Which top?", pick the ONE item from the inventory that best fits the weather.
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
@chat_bp.route("/chat-history", methods=["GET"])
def get_chat_history():
    user_id = get_current_user_id()
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    history = supabase.table("chat_history") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()
    
    return jsonify({"history": history.data})

# Inside your existing @chat_bp.route("/chat-message")
# Save User Message
    supabase.table("chat_history").insert({
        "user_id": user_id, 
        "role": "user", 
        "content": user_query
    }).execute()

    # ... (AI Logic) ...

    # Save AI Reply
    supabase.table("chat_history").insert({
        "user_id": user_id, 
        "role": "ai", 
        "content": reply
    }).execute()