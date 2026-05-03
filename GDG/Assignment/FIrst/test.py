import requests
from requests.exceptions import JSONDecodeError

BASE_URL = "http://127.0.0.1:3000"

def run_tests():
    print("Testing...")

    payload = {"username": "admin", "password": "secret"}

    login_response = requests.post(f"{BASE_URL}/login", json=payload)

    if login_response.status_code != 200:
        print("Login failed")
        print("Status:", login_response.status_code)
        print("Body:", login_response.text)
        return

    try:
        access_token = login_response.json().get("access_token")
    except JSONDecodeError:
        print("Login response was not JSON")
        print("Body:", login_response.text)
        return

    print("Logged in!")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    protected = requests.get(f"{BASE_URL}/protected", headers=headers)

    try:
        print("Protected response:", protected.json())
    except JSONDecodeError:
        print("Protected endpoint did not return JSON")
        print("Status:", protected.status_code)
        print("Content-Type:", protected.headers.get("content-type"))
        print("Body:", protected.text)

run_tests()