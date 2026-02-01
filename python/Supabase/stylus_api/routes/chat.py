from flask import Blueprint, request, jsonify
import google.generativeai as genai
from lib.supabase_client import supabase
from ..config import gem
chat_bp = Blueprint('chat', __name__)
gem_key = gem
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

@chat_bp.route('/api/chat-message', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message')

    # 1. Fetch user's wardrobe context so AI knows what they own
    items = supabase.table('wardrobe_items').select('*').eq('user_id', user_id).execute()
    wardrobe_summary = [f"{i['color']} {i['category']}" for i in items.data]

    # 2. Craft the System Prompt
    prompt = f"""
    You are 'Stylus', a professional AI fashion stylist. 
    The user owns: {', '.join(wardrobe_summary)}.
    User asks: {user_message}
    Give a concise, stylish, and helpful answer. Use emojis.
    """

    response = model.generate_content(prompt)
    bot_message = response.text

    # 3. Save to History (Supabase)
    supabase.table('chat_history').insert({
        "user_id": user_id,
        "message": user_message,
        "response": bot_message
    }).execute()

    return jsonify({"response": bot_message})