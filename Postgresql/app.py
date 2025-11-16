from flask import Flask

app = Flask(__name__)

@app.get("/")
#uses get method
def my_home():
    return "HIiiiiiiiiiiii"

app.run(port=2500)