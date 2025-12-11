#Pydantic is a python Library used for 
# data parsing and data validation using Python type hints.
#Validation If the client sends Data that doesn't match the pydantic model 
# (e.g they send "Two" instead of 2 for an int), Pydantic model immediately throws a clear validation error
#(HTTP 422), stopping the request before it hits your function logic.
#Serialization: It converts Python Objects into JSON and vice-versa
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

#3 Define Pydantic model for a book
#This model inherits from BaseModel and uses python type hints for validation.
class Book(BaseModel):
    title:str #Must be a string
    author:str #Must be a string
    year:int #Must be a integer
    #optional field: using 'None' as default makes it optional
    isbn: str | None = None

#4 Create a POST endpoint that consumes the Pydantic Model
@app.post("/books/")    
    def create_book(book:Book):#The magic: FastAPI expects a Book Object here
    #FastAPI automatically:
    # 1. Reads the JSON request body. 