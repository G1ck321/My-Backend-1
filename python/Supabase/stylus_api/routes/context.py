import requests
from flask import Blueprint, jsonify
from ..config import Config
context_bp = Blueprint('context', __name__)

key = Config.WEATHER
# Replace with a real key from OpenWeatherMap (Free tier)
WEATHER_API_KEY = key

@context_bp.route('/api/weather', methods=['GET'])
def get_weather():
    # Use a real API Key from OpenWeatherMap
    api_key = "YOUR_REAL_API_KEY" 
    city = "Lagos"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        
        if r.status_code == 200 and 'main' in data:
            return jsonify({
                "temp": data['main']['temp'],
                "condition": data['weather'][0]['main'],
                "success": True
            })
    except:
        pass

    # Safe Fallback
    return jsonify({"temp": 25, "condition": "Clear", "success": False})
def get_calendar(user_id):
    # Pulls from the new user_events table we created in SQL
    events = supabase.table('user_events').select('*').eq('user_id', user_id).execute()
    return jsonify(events.data)
@wardrobe_bp.route("/log-wear", methods=["POST"])
def log_wear():
    user_id = get_current_user_id()
    data = request.get_json()
    item_ids = data.get("item_ids") # Array of IDs worn

    # Log to the 'outfit_logs' table for Style Insights
    supabase.table("outfit_logs").insert({
        "user_id": user_id,
        "items": item_ids,
        "weather_context": get_weather().get_json()
    }).execute()
    
    return jsonify({"status": "logged"})