from flask import Flask, jsonify, send_from_directory,render_template,request
import json
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)
users = [
    {"user1": ["Aglfre", 21, "Full-Stack Developer"]},
    {"user2": ["Addl", 22, "Computer Engineer"]},
    {"user3": ["Ohdjd", 23, "Artificial Intelligence"]},
    
    
]


@app.route("/api/users")
def get_users():
    return jsonify()

@app.route("/")
def serve():
    # return send_from_directory('.', 'index.html')
    return render_template('index.html')

# users1 = {
#     "1":{"name":"James Paul","age":"44","Job":"Data Analyst"},
#     "2":{"name":"Flora Bell","age":"34","Job":"UI/UX Designer"}
    
# }
# @app.route('/api/users1')
# def get_users1():
#     return jsonify(users1)

# @app.after_request
# def after(response):
#     response.headers.add('Acess-Control-Allow-Origin','*')
#     response.headers.add('Acess-Control-Allow-Headers','Content-Type,Authorization ')
#     response.headers.add('Acess-Control-Allow-Methods','GET,PUT,POST,DELETE,OPTIONS')
#     return response
if __name__ == "__main__":
    app.run(port=5000, debug=True)
