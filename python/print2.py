users = [
    {"id":"user1",
    "username":"youre udhd",
    "age": 21,
    "job":"Full-Stack Developer"
    }
    
]
users1 = {
    "username":"yoddudhd",
    "age": 23,
    "job":"Artificial Intelligence"
    }
new_id = len(users)+1
print(new_id)
new_user = "user"+str(new_id)
print(new_user)
print(users)
users1.update({"id":new_user})
my_use = users.append(users1)
print(users)
