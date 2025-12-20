import requests
from datetime import timedelta, datetime
# created_at = datetime.utcnow()-timedelta(hours=2)
# pay = {"name":"Todo 9","created_at":str(created_at)}
users_email:str = "oluwagbemigaagbejimi@gmail.com"
users_password:str = "post456"
pay = {"email":users_email,"password":users_password}
pay2 = {"id":"2"}

# res = requests.get(url="http://127.0.0.1:5000/api/todo")
# print(res.text, "text", res,"sponse")
# res1 = requests.get(url="http://127.0.0.1:5000/api/user/1")
# print(res1.text, "text1", res,"sponse1")
res2 = requests.post(url="http://127.0.0.1:5000/api/login",json=pay)
print(res2.text, "text2", res2,"sponse2")
# res3 = requests.patch(url=f"http://127.0.0.1:5000/api/update_todo/{pay["id"]}",json=pay)
# print(res3.text, "text3", res3,"sponse3")
# res4 = requests.delete(url=f"http://127.0.0.1:5000/api/delete_todo/{pay2["id"]}")
# print(res4.text, "text4", res4,"sponse4")