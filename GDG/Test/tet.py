import requests
pay = {"firstName":"Jamyes","lastName":"Pauso","email":"gff@mm.xox"}
URL = "https://my-backend-1-s57s.onrender.com/webhooks/flutterwave"
response = requests.delete(URL)
print(response)
print(response.text)