import requests
pay = {"firstName":"Jamyes","lastName":"Pauso","email":"gff@mm.xox"}
URL = "http://127.0.0.1:3000/api/delete_note/22"
response = requests.delete(URL)
print(response)
print(response.text)