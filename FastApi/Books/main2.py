import uvicorn
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/ri")
def getReal(boot:str = Body(embed=True)):
    return f"{boot} is Dollar Income"

if __name__=="__main__":
    uvicorn.run("main2:app", reload=True, port=6000)

