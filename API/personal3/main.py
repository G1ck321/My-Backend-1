import os
import time
import base64
from typing import Optional

from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars (see .env.example)")

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

app = Flask(__name__, static_folder="static", template_folder="templates")

# Simple token cache
_token: Optional[str] = None
_token_expires_at: float = 0.0  # UNIX timestamp


def _request_token() -> dict:
    """Request a new token from Spotify (client credentials)."""
    auth = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64 = base64.b64encode(auth.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}
    resp = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_bearer_token() -> str:
    """Return a valid bearer token, refreshing early if necessary."""
    global _token, _token_expires_at
    now = time.time()
    # refresh 30 seconds before expiry to avoid edge cases
    if _token and now < (_token_expires_at - 30):
        return _token

    token_info = _request_token()
    access_token = token_info.get("access_token")
    expires_in = int(token_info.get("expires_in", 3600))
    if not access_token:
        raise RuntimeError("Failed to obtain access token from Spotify")
    _token = access_token
    _token_expires_at = now + expires_in
    return _token


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search-top-tracks", methods=["POST"])
def search_top_tracks():
    """
    Expects JSON: { "artist": "artist name", "country": "US" (optional) }
    Returns JSON with top tracks (max 5).
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON body"}), 400

    artist_name = (body.get("artist") or "").strip()
    country = body.get("country", "US").strip().upper() or "US"
    if not artist_name:
        return jsonify({"error": "Missing 'artist' in request body"}), 400

    try:
        token = get_bearer_token()
    except Exception as exc:
        return jsonify({"error": "auth_error", "message": str(exc)}), 500

    headers = {"Authorization": f"Bearer {token}"}
    # Search artist
    search_params = {"q": artist_name, "type": "artist", "limit": 1}
    search_resp = requests.get(f"{API_BASE}/search", headers=headers, params=search_params, timeout=10)
    if search_resp.status_code != 200:
        return jsonify({"error": "search_failed", "status": search_resp.status_code, "body": search_resp.text}), 502

    search_json = search_resp.json()
    artists = search_json.get("artists", {}).get("items", [])
    if not artists:
        return jsonify({"error": "not_found", "message": f"No artist found for '{artist_name}'"}), 404

    artist_id = artists[0]["id"]
    artist_name_clean = artists[0].get("name", artist_name)

    # Get top tracks (Spotify expects a country code)
    top_params = {"country": country}
    top_resp = requests.get(f"{API_BASE}/artists/{artist_id}/top-tracks", headers=headers, params=top_params, timeout=10)
    if top_resp.status_code != 200:
        return jsonify({"error": "top_tracks_failed", "status": top_resp.status_code, "body": top_resp.text}), 502

    top_json = top_resp.json()
    tracks = top_json.get("tracks", [])[:5]
    simplified = []
    for t in tracks:
        simplified.append({
            "name": t.get("name"),
            "album": t.get("album", {}).get("name"),
            "album_image": next(iter(t.get("album", {}).get("images", [])), {}).get("url"),
            "preview_url": t.get("preview_url"),
            "spotify_url": t.get("external_urls", {}).get("spotify"),
            "duration_ms": t.get("duration_ms"),
            "popularity": t.get("popularity"),
        })

    return jsonify({
        "artist": artist_name_clean,
        "artist_id": artist_id,
        "tracks": simplified,
    })


if __name__ == "__main__":
    # For local dev only; use a WSGI server (gunicorn/uwsgi) for production
    app.run(host="0.0.0.0", port=5000, debug=True)
