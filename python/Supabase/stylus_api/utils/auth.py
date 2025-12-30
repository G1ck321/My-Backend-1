# backend/stylus_api/utils/auth.py
import jwt
from flask import request, current_app

def get_current_user_id():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        print("DEBUG: No Bearer token found in header")
        return None

    # Extract the token
    token = auth_header.split(" ", 1)[1]
    
    try:
        # 1. Get the secret from your config (loaded from .env)
        jwt_secret = current_app.config["SUPABASE_JWT_SECRET"]
        
        # 2. Decode using HS256 (the Supabase default)
        # Note: we add audience="authenticated" because Supabase sets this in every token
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        print(f"DEBUG: Successfully verified user: {payload.get('sub')}")
        return payload.get("sub") # 'sub' is the unique User ID
        
    except jwt.ExpiredSignatureError:
        print("DEBUG: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"DEBUG: JWT Decode failed: {str(e)}")
        return None
    except Exception as e:
        print(f"DEBUG: Unexpected Auth Error: {str(e)}")
        return None