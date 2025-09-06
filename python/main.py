def list_meth():
    i: int = 0
    
    for method in dir(list):
        if "__" not in method:
            i+=1
            print(i, method,end="\n",sep=". ")
list_meth()