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

GEMINI_MODEL_NAME = "models/gemini-2.5-flash"
GEMMA_MODEL_NAME  = "models/gemma-3-4b-it"


# primary_model  = genai.GenerativeModel(PRIMARY_MODEL)
# fallback_model = genai.GenerativeModel(FALLBACK_MODEL)        # Cheaper fallback


# ==================================================
# SIMPLE IN-MEMORY RATE LIMIT
# ==================================================

def check_supabase(resp, action=""):
    """
    Safely check a Supabase APIResponse for errors.
    Compatible with different supabase-py versions.
    """
    if getattr(resp, "status_code", 200) >= 400:
        err = getattr(resp, "error", None) or resp.data
        print(f"⚠️ Supabase Error during {action}: {err}")
        
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
    now = time.time()
    last_call = LAST_CALL_TIME.get(user_id, 0)
    if now - last_call < cooldown_seconds:
        return False
    LAST_CALL_TIME[user_id] = now
    return True



# ==================================================
# AI GENERATION WITH SAFE FALLBACK
# ==================================================

def generate_ai_response(prompt: str):
    """
    Attempt Gemini first; fallback to Gemma on any error.
    Returns (response_text, model_name)
    """
    try:
        gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = gemini_model.generate_content(prompt)
        return response.text, GEMINI_MODEL_NAME
    except Exception as gemini_error:
        print(f"❌ Gemini Error: {gemini_error}")
        print("🔁 Falling back to Gemma")
    try:
        gemma_model = genai.GenerativeModel(GEMMA_MODEL_NAME)
        response = gemma_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.6,
                "top_p": 0.9,
                "max_output_tokens": 512
            }
        )
        return response.text, GEMMA_MODEL_NAME
    except Exception as gemma_error:
        print(f"🔥 Gemma Error: {gemma_error}")
        raise RuntimeError("All models failed")


# ==================================================
# BLUEPRINT
# ==================================================

chat_bp = Blueprint("chat", __name__)


# ==================================================
# CHAT ENDPOINT
# ==================================================

@chat_bp.route("/chat-message", methods=["POST"])
def chat():
    """
    Main chat endpoint. Steps:
    1. Authenticate user
    2. Rate-limit
    3. Fetch recent chat history
    4. Save user message
    5. Fetch weather and profile info
    6. Fetch wardrobe inventory
    7. Build AI system prompt
    8. Generate AI response
    9. Save AI response
    10. Return response
    """
    try:
        # ----------------------------
        # 1. AUTH & RATE LIMIT
        # ----------------------------
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"reply": "Unauthorized"}), 401

        if not rate_limit(user_id):
            return jsonify({"reply": "Hold on 😅 Wait a moment before asking again."}), 429

        data = request.get_json()
        current_agenda = data.get("agenda", "Class")
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({"reply": "Say something first 🙂"}), 400

        # ----------------------------
        # 2. FETCH RECENT CHAT HISTORY
        # ----------------------------
        history_resp = (
            supabase.table("chat_history")
            .select("role, content")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(14)
            .execute()
        )
        check_supabase(history_resp, "fetching chat history")
        history_rows = history_resp.data or []

        # Format chat history for AI (only last few messages)
        formatted_history = []
        for row in reversed(history_rows):
            speaker = "User" if row.get("role") == "user" else "StyluS"
            formatted_history.append(f"{speaker}: {row.get('content')}")
        GEMINI_HISTORY_LIMIT = 5
        chat_history_text = "\n".join(formatted_history[-GEMINI_HISTORY_LIMIT:])

        # ----------------------------
        # 3. SAVE USER MESSAGE
        # ----------------------------
        insert_resp = supabase.table("chat_history").insert({
            "user_id": user_id,
            "role": "user",
            "content": user_message
        }).execute()
        check_supabase(insert_resp, "saving user message")

        # ----------------------------
        # 4. FETCH WEATHER & PROFILE
        # ----------------------------
        raw_weather = get_weather().get_json()
        # Ensure dict, fallback to empty dict
        if isinstance(raw_weather, list) and raw_weather:
            weather = raw_weather[0]
        elif isinstance(raw_weather, dict):
            weather = raw_weather
        else:
            weather = {}
        temperature = weather.get("temp", 25)
        condition = weather.get("condition", "Clear")

        profile_resp = supabase.table("user_profiles").select("style_vibe, display_name").eq("user_id", user_id).execute()
        check_supabase(profile_resp, "fetching profile")
        profile_data = profile_resp.data
        # Supabase always returns a list for .select
        if isinstance(profile_data, list) and profile_data:
            profile = profile_data[0]
        elif isinstance(profile_data, dict):
            profile = profile_data
        else:
            profile = {}
        style_vibe = profile.get("style_vibe", "Versatile")
        display_name = profile.get("display_name", "User")

        # ----------------------------
        # 5. FETCH WARDROBE INVENTORY
        # ----------------------------
        wardrobe_resp = supabase.table("wardrobe_items").select("category, color, tags").eq("user_id", user_id).execute()
        check_supabase(wardrobe_resp, "fetching wardrobe")
        wardrobe_items = wardrobe_resp.data or []

        # Format inventory lines for AI
        inventory_lines = []
        for item in wardrobe_items:
            tags = [str(t) for t in (item.get("tags") or []) if t]
            category = item.get("category") or "item"
            if not tags or (len(tags) == 1 and tags[0].lower() == "clothing"):
                continue
            color = item.get("color") or ""
            line = f"- {color} {category}: {', '.join(tags)}"
            inventory_lines.append(line)
        if not inventory_lines:
            inventory_lines = ["Your wardrobe is currently being processed by AI. Please wait for tags to generate."]

        # ----------------------------
        # 6. MAP AGENDA → STYLE RULE
        # ----------------------------
        agenda_rules = {
            "Internship": "Strict professional. If a tie/blazer exists, use it.",
            "Class": "Academic smart-casual. Layering preferred for lecture halls.",
            "Social": "Relaxed but stylish. Prioritize comfort and campus vibe."
        }
        specific_rule = agenda_rules.get(current_agenda, "")

        # ----------------------------
        # 7. BUILD AI SYSTEM PROMPT
        # ----------------------------
        system_prompt = f"""
### IDENTITY
You are StyluS, a high-end fashion consultant specializing in "University Corporate" and "Campus Casual" aesthetics. Be decisive and analytical.

### CONTEXT
- User Name: {display_name}
- User Aesthetic: {style_vibe}
- Current Agenda: {current_agenda} ({specific_rule})
- Weather: {temperature}°C, {condition}
- Closet Inventory: {inventory_lines}

### OPERATIONAL ALGORITHM
1. ANALYZE WEATHER: Layering under 18°C, breathable above 24°C
2. SCAN INVENTORY: Match items to Weather & User Aesthetic
3. MATCH COLORS: Complementary top/bottom
4. FINALIZE: ONE top + ONE bottom/accessory

### STYLISTIC CONSTRAINTS
- NO FILLERS or HEDGING
- NO UNKNOWNS
- VIBE FOCUS: Prioritize items based on Aesthetic

### OUTPUT FORMAT
**[Outfit Name]**
- **Top**: [Item Color] [Item Category]
- **Bottom**: [Item Color] [Item Category]
- **Accessory**: [Item Category] (if applicable)
**Reasoning**: [1-2 sentences]
"""
        final_prompt = f"{system_prompt}\n\nUser Question: {user_message}"

        # ----------------------------
        # 8. GENERATE AI RESPONSE
        # ----------------------------
        ai_reply, model_used = generate_ai_response(final_prompt)

        # ----------------------------
        # 9. SAVE AI RESPONSE
        # ----------------------------
        save_ai_resp = supabase.table("chat_history").insert({
            "user_id": user_id,
            "role": "ai",
            "content": ai_reply
        }).execute()
        check_supabase(save_ai_resp, "saving AI response")

        # ----------------------------
        # 10. RETURN RESPONSE
        # ----------------------------
        return jsonify({
            "reply": ai_reply,
            "model": model_used,
            "weather": {"temp": temperature, "condition": condition}
        })

    except Exception as error:
        print("🔥 Chat Error:", error)
        return jsonify({"reply": "I'm having a fashion brain freeze 😵 Try again shortly."}), 500

# ==================================================
# GET /chat-history
# ==================================================
@chat_bp.route("/chat-history", methods=["GET"])
def get_chat_history():
    """
    Paginated fetch of user's chat history.
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))

        response = (
            supabase.table("chat_history")
            .select("id, role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        check_supabase(response, "fetching chat history")

        return jsonify({
            "history": response.data or [],
            "hasMore": len(response.data or []) == limit
        }), 200

    except Exception as e:
        print(f"❌ History Error: {e}")
        return jsonify({"error": "Could not load history"}), 500

# ==================================================
# POST /clear-chat
# ==================================================
@chat_bp.route("/clear-chat", methods=["POST"])
def clear_chat():
    """
    Deletes all chat history for the current user.
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        delete_resp = supabase.table("chat_history").delete().eq("user_id", user_id).execute()
        check_supabase(delete_resp, "clearing chat")

        return jsonify({"success": True, "message": "Chat cleared successfully."}), 200

    except Exception as e:
        print(f"❌ Clear Chat Error: {e}")
        return jsonify({"error": "Could not clear chat"}), 500