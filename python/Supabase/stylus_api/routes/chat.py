from flask import Blueprint, request, jsonify
import google.generativeai as genai
import time

from .profile import supabase
from ..routes.context import get_weather
from ..utils.auth import get_current_user_id
from ..config import Config


# ==================================================
# AI MODEL CONFIGURATION
# ==================================================

genai.configure(api_key=Config.GEM)

GEMINI_MODEL = "gemini-flash-latest"   # Smart, fast, limited quota
GEMMA_MODEL  = "gemma-3-4b-it"         # Cheaper fallback


# ==================================================
# SIMPLE IN-MEMORY RATE LIMIT
# ==================================================

genai.configure(api_key=Config.GEM)

def list_available_models():
    print("--- Available Stylus-Compatible Models ---")
    for m in genai.list_models():
        # Look for models that support content generation
        if 'generateContent' in m.supported_generation_methods:
            # Note: 'gemini-1.5-flash' is the best free-tier model for Vision
            # 'gemma' models are typically text-only in this SDK
            print(f"Model Name: {m.name}")
            print(f"Description: {m.description}")
            print(f"Capabilities: {m.supported_generation_methods}\n")

# Run this once in your terminal to see the list
# list_available_models()
LAST_CALL_TIME = {}

def rate_limit(user_id: str, cooldown_seconds: int = 3) -> bool:
    """
    Allow one request per user every `cooldown_seconds`.
    Prevents spam and accidental quota burn.
    """
    now = time.time()
    last_call = LAST_CALL_TIME.get(user_id, 0)

    if now - last_call < cooldown_seconds:
        return False

    LAST_CALL_TIME[user_id] = now
    return True


# ==================================================
# AI GENERATION WITH SAFE FALLBACK
# ==================================================

def generate_ai_response(prompt: str) -> tuple[str, str]:
    """
    1. Try Gemini first
    2. Fall back to Gemma only on quota / rate limit errors
    """

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text, GEMINI_MODEL

    except Exception as error:
        error_text = str(error).lower()

        quota_errors = [
            "429",
            "quota",
            "rate",
            "exceeded",
            "resource_exhausted"
        ]

        if not any(code in error_text for code in quota_errors):
            raise

        print("⚠️ Gemini unavailable, falling back to Gemma")

        # Gemma performs best with short prompts
        shortened_prompt = prompt[:2000]

        fallback_model = genai.GenerativeModel(GEMMA_MODEL)
        response = fallback_model.generate_content(shortened_prompt)

        return response.text, GEMMA_MODEL


# ==================================================
# BLUEPRINT
# ==================================================

chat_bp = Blueprint("chat", __name__)


# ==================================================
# CHAT ENDPOINT
# ==================================================

@chat_bp.route("/chat-message", methods=["POST"])
def chat():
    try:
        # ------------------------------------------
        # 1. AUTH & BASIC GUARDS
        # ------------------------------------------
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"reply": "Unauthorized"}), 401

        if not rate_limit(user_id):
            return jsonify({"reply": "Hold on 😅 Give me a second before asking again."}), 429

        data = request.get_json()
        user_message = (data.get("message") or "").strip()

        if not user_message:
            return jsonify({"reply": "Say something first 🙂"}), 400

        # ------------------------------------------
        # 2. FETCH RECENT CHAT HISTORY
        # ------------------------------------------
        history_rows = (
            supabase
            .table("chat_history")
            .select("role, content")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(14)
            .execute()
            .data
        )

        # Format history into readable conversation text
        formatted_history = []
        for row in reversed(history_rows or []):
            speaker = "User" if row["role"] == "user" else "StyluS"
            formatted_history.append(f"{speaker}: {row['content']}")

        GEMINI_HISTORY_LIMIT = 5
        chat_history_text = "\n".join(formatted_history[-GEMINI_HISTORY_LIMIT:])

        # ------------------------------------------
        # 3. SAVE USER MESSAGE
        # ------------------------------------------
        supabase.table("chat_history").insert({
            "user_id": user_id,
            "role": "user",
            "content": user_message
        }).execute()

        # ------------------------------------------
        # 4. FETCH CONTEXT (WEATHER + STYLE VIBE)
        # ------------------------------------------
        weather = get_weather().get_json()
        temperature = weather.get("temp", 25)
        condition = weather.get("condition", "Clear")

        profile = (
            supabase
            .table("profiles")
            .select("style_vibe")
            .eq("id", user_id)
            .maybe_single()
            .execute()
            .data
        )

        style_vibe = (profile.get("style_vibe") if profile and profile.get("style_vibe") else "Versatile")

        # ------------------------------------------
        # 5. FETCH USER WARDROBE
        # ------------------------------------------
        wardrobe_items = (
            supabase
            .table("wardrobe_items")
            .select("category, color, tags")
            .eq("user_id", user_id)
            .execute()
            .data
        )

        # ------------------------------------------
        # 6. FORMAT INVENTORY LINES SAFELY (FIX)
        # ------------------------------------------
        inventory_lines = []
        for item in wardrobe_items:
            category = item.get('category', 'unknown')
            color = item.get('color') or 'Neutral'  # Avoid None
            tags = [str(t) for t in (item.get("tags") or []) if t]  # Remove None from tags
            line = f"{category} ({color})"
            if tags:
                line += f" – {', '.join(tags)}"
            inventory_lines.append(line)

        # ------------------------------------------
        # 7. BUILD SYSTEM PROMPT
        # ------------------------------------------
        system_prompt = f"""
You are StyluS, a professional fashion consultant. 
User's Aesthetic: {style_vibe}
Weather: {temperature}°C, {condition}.

USER'S CLOSET:
{inventory_lines}

STRICT RULES:
1. NEVER use the word "unknown." If data is missing, describe the item by its ID.
2. BE DECISIVE. Do not say "I suggest a top." Say "Wear the [ID: 123] Grey Streetwear Top."
3. REASONING: Explain why that specific item works for {temperature}°C. (e.g., "Grey is a neutral that won't absorb too much heat under the {condition} sky.")
4. If the user asks a follow-up, refer to the IDs mentioned in the chat history.
"""

        # ------------------------------------------
        # 8. GENERATE AI RESPONSE
        # ------------------------------------------
        ai_reply, model_used = generate_ai_response(system_prompt)

        # ------------------------------------------
        # 9. SAVE AI RESPONSE
        # ------------------------------------------
        supabase.table("chat_history").insert({
            "user_id": user_id,
            "role": "ai",
            "content": ai_reply
        }).execute()

        # ------------------------------------------
        # 10. RETURN RESPONSE
        # ------------------------------------------
        return jsonify({
            "reply": ai_reply,
            "model": model_used,
            "weather": {
                "temp": temperature,
                "condition": condition
            }
        })

    except Exception as error:
        print("🔥 Chat Error:", error)
        return jsonify({
            "reply": "I'm having a fashion brain freeze 😵 Try again shortly."
        }), 500

@chat_bp.route("/chat-history", methods=["GET"])
def get_chat_history():
    """
    Fetches paginated chat history for the logged-in user.
    Query Params:
        limit: Number of messages to fetch (default 10)
        offset: Number of messages to skip (for pagination)
    """
    try:
        # 1. Authenticate User
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        # 2. Get Pagination Parameters
        # limit: how many rows to fetch
        # offset: where to start (e.g., offset 10 starts at the 11th row)
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))

        # 3. Query Supabase
        # .order() ensures we get the most recent messages first
        # .range() handles the pagination logic
        response = (
            supabase.table("chat_history")
            .select("id, role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True) 
            .range(offset, offset + limit - 1)
            .execute()
        )

        # 4. Return data
        # Note: We return it 'as is', but the frontend may need to .reverse() 
        # it to show chronologically (oldest at top).
        return jsonify({
            "history": response.data,
            "hasMore": len(response.data) == limit
        }), 200

    except Exception as e:
        print(f"❌ History Error: {str(e)}")
        return jsonify({"error": "Could not load history"}), 500