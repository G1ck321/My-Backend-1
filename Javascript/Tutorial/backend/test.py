# import requests
# pay = {"firstName":"Jamyes","lastName":"Pauso","email":"gff@mm.xox"}
# URL = "http://127.0.0.1:5000/create_contact"
# response = requests.post(URL,json=pay)
# print(response)
# print(response.text)
import requests
pay = {"firstName":"Jamyes","lastName":"Pauso","email":"gff@mm.xox"}
URL = "http://127.0.0.1:5000/delete_contact/5"
response = requests.delete(URL)
print(response)
print(response.text)