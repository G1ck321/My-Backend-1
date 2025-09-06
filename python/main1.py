






from collections import deque
people: list[str] = ["Gbemi","Jumo","Kola"]
print(people)
people.append("hii")
print(people)
q:deque[str] = deque(people)

q.appendleft("Sharp")
print(q.__contains__("hii"))
#help(q)

print(q)

people.clear()
print(people)
p = q.copy()
print(p)
print(p.reverse)