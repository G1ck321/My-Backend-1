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
    1. Try Gemini ONCE
    2. On ANY Gemini error → fall back to Gemma
    3. Never retry Gemini
    """

    # --- Try Gemini first ---
    try:
        gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = gemini_model.generate_content(prompt)
        return response.text, GEMINI_MODEL_NAME

    except Exception as gemini_error:
        error_msg = str(gemini_error)
        print(f"❌ Gemini Error: {error_msg}")
        print("🔁 Falling back to Gemma")

    # --- Fallback to Gemma ---
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
            # SKIP items that are still in "failed" or "pending" status
            # or items that only have the generic fallback tags
            tags = [str(t) for t in (item.get("tags") or []) if t]
            category = item.get('category', 'item')
            
            # If the only tag is 'clothing' or the category itself, the AI hasn't fixed it yet
            if not tags or (len(tags) == 1 and tags[0] == 'clothing'):
                continue 

            color = item.get('color') or ''
            line = f"- {color} {category}: {', '.join(tags)}"
            inventory_lines.append(line)

        # If inventory is empty after filtering
        if not inventory_lines:
            inventory_lines = ["Your wardrobe is currently being processed by AI. Please wait for tags to generate."]

        # ------------------------------------------
        # 7. BUILD SYSTEM PROMPT
        # ------------------------------------------
        profile_data = supabase.table("profiles").select("display_name").eq("id", user_id).maybe_single().execute().data
        display_name = profile_data.get("display_name", "User") if profile_data else "User"
        system_prompt = f"""
### IDENTITY
You are StyluS, a high-end fashion consultant specializing in "University Corporate" and "Campus Casual" aesthetics. You are decisive, sophisticated, and analytical. You never hedge.

### CONTEXT
- User Name: {{user_name}}
- User Aesthetic: {{style_vibe}}
- Weather: {{temperature}}°C, {{condition}}
- Closet Inventory: {{inventory_lines}}

### OPERATIONAL ALGORITHM (Chain of Thought)
1. ANALYZE WEATHER: Evaluate if the temperature requires layering (under 18°C) or breathability (over 24°C).
2. SCAN INVENTORY: Identify specific items in the Closet Inventory that match the Weather and User Aesthetic.
3. MATCH COLORS: Ensure the selected top and bottom have complementary colors.
4. FINALIZE: Select ONE specific top and ONE specific bottom/accessory.

### STYLISTIC CONSTRAINTS
- NO FILLERS: Do not start with "Sure," "Okay," or "I can help with that."
- NO HEDGING: Use "Wear the..." instead of "I suggest..." or "You could try..."
- NO UNKNOWNS: Never use the word "unknown." If data is missing, describe the item by its Category.
- VIBE FOCUS: If Vibe is "University Corporate," prioritize Blazers, Ties, and Chinos.

### OUTPUT FORMAT
**[Outfit Name]**
- **Top**: [Item Color] [Item Category]
- **Bottom**: [Item Color] [Item Category]
- **Accessory**: [Item Category] (if applicable)

**Reasoning**: [1-2 sentences explaining the choice based on temperature and aesthetic.]
"""
        # Build the final prompt for the AI
        final_prompt = system_prompt.replace("{{user_name}}", display_name)\
                             .replace("{{style_vibe}}", style_vibe)\
                             .replace("{{temperature}}", str(temperature))\
                             .replace("{{condition}}", condition)\
                             .replace("{{inventory_lines}}", str(inventory_lines))

# Add the user's actual question at the end
        full_input = f"{final_prompt}\n\nUser Question: {user_message}"

        ai_reply, model_used = generate_ai_response(full_input)
        # ------------------------------------------
        # 8. GENERATE AI RESPONSE
        # ------------------------------------------

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
# ==================================================
# POST /clear-chat → Clears all messages for the current user
# ==================================================
@chat_bp.route("/clear-chat", methods=["POST"])
def clear_chat():
    """
    Clears all chat history for the logged-in user.
    Frontend calls this when the "Clear chats" button is pressed.
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        # Delete all messages for this user
        supabase.table("chat_history").delete().eq("user_id", user_id).execute()

        return jsonify({"success": True, "message": "Chat cleared successfully."}), 200

    except Exception as e:
        print(f"❌ Clear Chat Error: {e}")
        return jsonify({"error": "Could not clear chat"}), 500
