# backend/app.py
from stylus_api import create_app
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from stylus_api import get_current_user_id
load_dotenv()
app = create_app()


@app.route("/api/health", methods=["GET"])
def health():
    return {"status": "Flask running!", "user_id": get_current_user_id()}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
