from flask import Flask, jsonify, request
from config import app, supabase, news_key
import requests
from dotenv import load_dotenv
import os
load_dotenv()
# --- NEWS API CONFIGURATION ---
NEWS_API_KEY = news_key
NEWS_URL = "https://newsapi.org/v2/everything"

@app.route("/api/news", methods=["GET"])
def get_personalized_news():
    """
    Fetches news based on the user's specific skills to mimic a 
    professional marketplace (Fiverr-style personalization).
    """
    user_id = request.args.get("user_id")
    if user_id == "re":
        return jsonify({"Jel":"uy"})
    
    try:
        # 1. Get user skills from Supabase
        profile = supabase.table("profiles").select("skills").eq("id", user_id).single().execute()
        skills = profile.data.get("skills", []) if profile.data else []
        
        # 2. Build search query based on skills (or default to general tech)
        query = " OR ".join(skills) if skills else "technology"
        print(query)
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 3,
            "apiKey": NEWS_API_KEY
        }
        
        response = requests.get(NEWS_URL, params=params)
        data = response.json()
        
        return jsonify(data.get("articles", [])), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/profile/update", methods=["POST"])
def update_profile():
    """
    Updates user profile details including skills and bio.
    """
    data = request.json
    user_id = data.get("user_id")
    updates = {
        "full_name": data.get("full_name"),
        "bio": data.get("bio"),
        "skills": data.get("skills"), # Expected as a list/array
        "avatar_url": data.get("avatar_url")
    }
    
    try:
        result = supabase.table("profiles").update(updates).eq("id", user_id).execute()
        return jsonify({"status": "success", "data": result.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ =="__main__":
    app.run(host="0.0.0.0", port=3030, debug=True)
    

    