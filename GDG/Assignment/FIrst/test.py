import requests

app = requests.get("http://127.0.0.1:3000")
print(app.text)

import requests, json

BASE_URL = "127.0.0.1:3000"

def run_tests():
    print(" Testing 1 2 3")

    payload = {"username": "admin", "password":"secret"}
    #send post request
    login_response = requests.post(f"{BASE_URL}/login",json=payload)

    if login_response.status_code != 200:
        print("Login Failed Is your server running")
        return 
    #Get the token from respone
    tokens = login_response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    print("Logged in pa!")

    #We have to pass the JWT in the headers to access protected, It's standard
    access_headers = {"Authorization":f"Bearer{access_token_token}"}
    login_response = requests.get(f"{BASE_URL}/protected",headers=access_headers)
    print("Logged in access token received accesstoken of", access_token[0:5])
    #To access the refresh token 
    refresh_headers = {"Authorization":f"Bearer{refresh_token_token}"}
    refresh_response = requests.post(f"{BASE_URL}/refresh",headers=refresh_headers)
    print("Logged in access token received accesstoken of", access_token[0:5])

    if refresh_response.status_code == 200:
        new_access = refresh_response.json().get("access_token")
        print("Token refreshed new one is ..", refresh_token[0:6],"...")
    else:
        print("Refresh failed.")
    
run_tests()