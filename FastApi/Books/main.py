from fastapi import FastAPI, Body, Header, Response
import sqlite3, hashlib, secrets
from services.hash import verify_password, hash_password



def create_relation():
    with sqlite3.connect("mock.db") as conn:
        db = conn.cursor()
    # AUTO INCREMENT not needed
        db.execute("""
    CREATE TABLE IF NOT EXISTS users(ID INTEGER PRIMARY KEY, 
    NAME VARCHAR,
     password_hash VARCHAR, 
    LOCATION VARCHAR,
    CURRENCY CHAR(20))""")
        return db, conn


# create_relation()

# execute()
app = FastAPI()

@app.get("/hi")
def greet():
    return "Hello? World?"

@app.get("/hi/{who}")
def greet(who):
    return f"Hello World!!, {who}"

#Path Parameter
@app.get("/hii")
def greet(who:str):
    # This is a required parameters
    return f"Hiiii {who}"

#Query Parameter ?= blah
@app.post("/hi")
def greet(name:str = Body(embed=True)):
    return f"My name is not {name} it is Gbemiga"

@app.get("/hider")
def greet(name:str = Header()):
    return f"My name is not {name} it is Gbemiga"

@app.get("/agent")
def userAgent(user_agent:str=Header()):
    return user_agent

#You can use more than one of this methods in a path function, 
# whetehr it be through:
#  URL
#  Query parameters
# the HTTP body, 
# HTTP headers
# cookies and so on
# You can create your own dependency function for pagination and authentication

# Let me try that out

@app.post("/userdata")
def authFunction(name:str = Body(embed=True), passwordhash:str= Header()):
    phash = hash_password(passwordhash)
    # verify with bcrypt.verify(password, hash)
    return phash, passwordhash, name, verify_password(passwordhash, phash)
    # successful

#send response via header
@app.get("/headina/{name}/{value}")
def header(name:str, value:str, response:Response ):
    response.headers[name] = value
    return "normal body"


if __name__=="__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, port=4000, host="0.0.0.0")