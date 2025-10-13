import csv
from pprint import pprint
path = "Book1.csv"
name = []
name = dict(name)
print(name)
with open(path, "r",newline="") as file:
    writer = csv.reader(file)
    for write in writer:
        if write[1] not in name.values():
            name[write[0].title()] =  write[1]
        
        
name = pprint(name)

