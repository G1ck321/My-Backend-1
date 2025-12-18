# import secrets
# print(secrets.token_hex(32))
import requests
response = requests.patch("http://127.0.0.1:3500/api/update_users/2", json={"username":"HelloWorld"})
# 
print(response.text)