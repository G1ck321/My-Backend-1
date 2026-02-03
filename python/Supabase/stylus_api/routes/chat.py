from flask import Blueprint, request, jsonify
from google import genai # NEW PACKAGE
from google.genai import types
from .profile import supabase
from ..routes.context import get_weather
from ..utils.auth import get_current_user_id
from ..config import Config
gem_key = Config.GEM

chat_bp = Blueprint('chat', __name__)
client = genai.Client(api_key=gem_key)

@chat_bp.route('/chat-message', methods=['POST'])
def chat():
    # 1. FIX: Define the user_id (Bouncer check)
    user_id = get_current_user_id() 
    
    data = request.json
    user_query = data.get('message')

    # 2. Get Weather (Safe Handling to avoid KeyError 'main')
    weather_res = get_weather().get_json()
    temp = weather_res.get('temp', 25) # Default to 25 if API fails
    cond = weather_res.get('condition', "Clear")

    # 3. Get Wardrobe (So Gemini knows what Chioma owns)
    # The 'user_id' is now defined above, fixing your NameError
    wardrobe_data = supabase.table('wardrobe_items').select('*').eq('user_id', user_id).execute()
    items_list = [f"{i['category']} ({i.get('color', 'unknown')})" for i in wardrobe_data.data]

    # 4. Build the AI Context (Per AI Style Assistant Doc)
    system_prompt = f"""
    You are the StyluS AI Assistant. 
    Weather in Lagos: {temp}°C, {cond}.
    User's Wardrobe: {", ".join(items_list) if items_list else "Empty"}.
    
    User Query: {user_query}
    
    Task: Give a friendly, conversational style tip. 
    If they ask 'What should I wear?', suggest items from their wardrobe list above.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(system_prompt)
        
        # 5. Logging (As required by MVP Doc)
        # You should save this interaction to a chat_history table here
        
        return jsonify({
            "reply": response.text,
            "weather": {"temp": temp, "condition": cond}
        })
    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"reply": "I'm having a bit of a fashion block. Try again in a second!"}), 500