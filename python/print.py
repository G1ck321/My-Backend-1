# from pprint import pprint
# users = [
#     {"user1": ["Agbejimi Oluwagbemiga", 21, "Full-Stack Developer"]},
#     {"user2": ["Akinyemi Kolade", 22, "Computer Engineer"]},
#     {"user3": ["Oyinloye Olaoluwa", 23, "Artificial Intelligence"]},
    
# ]
# print(users)
users = [
    {"id":"user1",
    "username":"youre udhd",
    "age": 21,
    "job":"Full-Stack Developer"
    }
    
]
print(users[0].get("user1"))
# if not all(key in users for key in ['username','age','job']):
# if not all (key in users  ):
prac= {"first":1,"second":2,"third":3}
prac1= {"first":"","second":2,"third":3}
prac2 = ["",1,2]
if  all(p in prac1  for p in ["first","second","third"]):
    print(all([p in prac1 for p in ["first","second","third"]]))
print(all(p for p in prac2))
listcomp = [key for key in users[0]]
print(listcomp)
for i,p in enumerate(users):
                print(i)