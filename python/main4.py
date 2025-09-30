from flask import Flask, jsonify, send_from_directory,render_template
import json


app = Flask(__name__)
users = [
    {"user1": ["Agbejimi Oluwagbemiga", 21, "Full-Stack Developer"]},
    {"user2": ["Akinyemi Kolade", 22, "Computer Engineer"]},
    {"user3": ["Oyinloye Olaoluwa", 23, "Artificial Intelligence"]},
    
]


@app.route("/api/users")
def get_users():
    return jsonify(users)

@app.route("/")
def serve():
    # return send_from_directory('.', 'index.html')
    return render_template('index.html')

@app.after_request
def after(response):
    response.headers.add('Acess-Control-Allow-Origin','*')
    response.headers.add('Acess-Control-Allow-Headers','Content-Type,Authorization')
    response.headers.add('Acess-Control-Allow-Methods','GET,PUT,POST,DELETE,OPTIONS')
    return response
if __name__ == "__main__":
    app.run(port=5000, debug=True)
