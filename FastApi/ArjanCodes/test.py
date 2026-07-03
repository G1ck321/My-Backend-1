from enum import Enum
import requests
import pprint

class Color(Enum):
    red = 4
    blue = 3
    green = 9

print(Color.blue)
print(type(Color.green))


response = requests.get(url="http://127.0.0.1:8000/")
pprint.pprint(response.json())

response = requests.get(url="http://127.0.0.1:8000/items/2")
pprint.pprint(response.json())

response = requests.get(url="http://127.0.0.1:8000/items?name=Pliers")
print(response.json())