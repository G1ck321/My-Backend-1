from fastapi import FastAPI
#1 Create FastAPI instance

app = FastAPI()

#Defines a route
@app.get("/")
def read_root():
    #FastAPI automatically converts the returned python dictionary 
    #as JSON response
    return {"Message":"Hello World, This is Gbemiga's First FastAPI  app"}

#You run the app by doing uvicorn main(filename):app(FastAPI instance name) --reload