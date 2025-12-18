import requests
<<<<<<< Updated upstream
payload = {"username":"DABw","password":"newrt@4444s"}
site= "http://127.0.0.1:3500/signup"
#htp:// must be specifieds
response = requests.post(url=site, json=payload)
print(response.status_code, "code", response.text,"text")
=======
payload = {"title":"Deep Work","author":"Cal Newport","year":"2008"}
site= "http://127.0.0.1:8000/books"
#htp:// must be specifieds
response = requests.post(url=site, json=payload)
print(response.status_code, "code", response.text, "text")
>>>>>>> Stashed changes
# response2 = requests.get(url = "https://google-mrwa.onrender.com/hello") 
# print(response2.text, response2.status_code)