import requests

app = requests.get("http://127.0.0.1:3000")
print(app.text)