import requests
url = "http://127.0.0.1:5002/api/users1/1"
pay = {"1":{"name":"James Paulo","age":"44","Job":"Data Analyst"}}
response = requests.put(url,json=pay)
print(response.json())