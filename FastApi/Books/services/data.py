
def get(data):
    if data:
        print("Here", data) 
    else: 
        print("Nothing")

def create(data):
    if data:
        print("created") 
        for d in data:
            print("d",end="")
    else: 
        print("Nothing")