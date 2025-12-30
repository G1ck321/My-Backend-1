from flask import Blueprint, request, jsonify
from ..utils.auth import get_current_user_id
from ..services.supabase import call_rpc

events_bp = Blueprint("events", __name__)

@events_bp.route("", methods=["GET"])
def get_events():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    
    events = call_rpc("get_user_events", {"p_user_id": user_id})
    return jsonify({"events": events})

@events_bp.route("", methods=["POST"])
def create_event():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.get_json() or {}
    
    event = call_rpc("create_event", {
        "p_user_id": user_id,
        "p_name": data.get("name"),
        "p_event_date": data.get("event_date"),
        "p_type": data.get("type")
    })
    
    return jsonify({"event": event}), 201
