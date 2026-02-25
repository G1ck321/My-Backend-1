

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
p = [name for name in  q]
print(p,"pp")
p.reverse()
#If you print p.reverse you get none
print(p)