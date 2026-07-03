from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()

#helper classes
class Category(Enum):
    TOOLS = "tools"
    CONSUMABLES = "consumables"

class Item(BaseModel):
    name:str
    price:float
    count:int
    id:int
    category:Category

items = {

    0:Item(name="Hammer", price=9.99, count=20, id=0, category=Category.TOOLS),
    1: Item(name="Pliers", price=5.99, count=34, id=1, category=Category.TOOLS),
    2: Item(name="Nails", price=43.99, count=40, id=3, category=Category.CONSUMABLES),

}

#FastAPI uses JSON serialisation and deserialisation for us.
#We can simply use built-in python and Pydantic types, use dict[int,Item]

@app.get("/")
def index()-> dict[str, dict[int, Item]]:
    return {"items":items}

@app.get("/items/{item_id}")
def query_itemid(item_id:int)->Item:
    if item_id not in items:
        #Fastai validates it is int
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} does not exist. ")
    return items[item_id]

#Function parameters that are not path parameters can be specified as query parameters
#Here we can query /items?count=20

Selection = dict[str, str | int | float | Category | None #Helper type
] #Dictionary containing the user's query arguments

@app.get("/items/")
def query_item_by_parameters(
    name:str | None = None,#For optionality
    price:float | None = None,
    count:int | None = None,
    category: Category | None = None,
    ):
    # )-> dict[str, Selection]:
    #Helper function that checks the values of what was given and returns true or false
    def check_item(item:Item)->bool:
        return all(
            (
            name is None or item.name == name,
            price is None or item.price == price,
            count is None or item.count == count,
            category is None or item.category ==  category)
        )
    selection = [item for item in items.values() if check_item(item)]

    return{
        "query":{
            "name":name, "price":price, "count":count, "category":category
            },
            "selection":selection,# Kept outside or raw to let FastAPI serialize the list of Pydantic models
        
    }
    