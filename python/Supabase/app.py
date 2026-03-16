# backend/app.py
from stylus_api import create_app
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from stylus_api import get_current_user_id

load_dotenv()
app = create_app()


 # ==========================================
    # HEALTH CHECK ENDPOINT (Keep Render warm)
    # ==========================================
    # Called by frontend after login to prevent free tier spin-down
@app.route("/api/health", methods=["GET"])
def health():
    """
    Health check endpoint to keep backend alive on Render free tier
    Render spins down after 15 min inactivity, this ping keeps it warm
    """
    try:
        user_id = get_current_user_id()
        return jsonify({
            "status": "Flask running!",
            "user_id": user_id or "anonymous",
            "timestamp": str(__import__('datetime').datetime.now())
        }), 200
    except Exception as e:
        return jsonify({
            "status": "Flask running!",
            "error": str(e),
            "timestamp": str(__import__('datetime').datetime.now())
        }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
