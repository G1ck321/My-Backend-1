# backend/stylus_api/utils/auth.py - FIXED
import jwt
import requests
from flask import request, current_app
import json

def get_current_user_id():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    
    try:
        # FIXED: Correct Supabase JWKS endpoint
        jwks_url = f"{current_app.config['SUPABASE_URL']}/.well-known/jwks.json"
        print(f"🔍 Fetching JWKS from: {jwks_url}")  # DEBUG
        
        res = requests.get(jwks_url, timeout=5)
        if res.status_code != 200:
            print(f"❌ JWKS failed: {res.status_code}")
            return None
            
        jwks = res.json()
        print(f"✅ JWKS loaded: {len(jwks['keys'])} keys")  # DEBUG
        
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        
        if not key:
            print(f"❌ No JWKS key for kid: {header['kid']}")
            return None
            
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token, 
            public_key, 
            algorithms=["RS256"], 
            audience="authenticated"
        )
        print(f"✅ User verified: {payload['sub'][:8]}...")  # DEBUG
        return payload["sub"]
        
    except Exception as e:
        print(f"❌ JWT decode failed: {str(e)}")
        return None
