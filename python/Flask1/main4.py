from flask import Flask, jsonify, send_from_directory,render_template,request
import json
from flask_cors import CORS
import requests
import psycopg2

app = Flask(__name__)
CORS(app)
users = [
    {"id":"user1",
    "username":"Agbejimi Oluwagbemiga",
    "age": 21,
    "job":"Full-Stack Developer"
    },

    {"id":"user2",
    "username":"Akinyemi Kolade",
    "age": 22,
    "job":"Computer Engineer"
    },

    {"id":"user3",
    "username":"Oyinloye Olaoluwa",
    "age": 23,
    "job":"Artificial Intelligence"
    }
    
]
def get_connected():
    conn = psycopg2.connect(
        host = 'localhost',
        user = 'postgres',
        database = 'Dvd',
        password = 'Sample@321'
    )
    return conn
def postgre():
    conn = get_connected()
    cur = conn.cursor()
    cur.execute("Select * from cars")
    rows = cur.fetchall()
    output = []
    id = 0
    for row in rows:
        car_data = {'brand':row[0],'model':row[1],'year':row[2]}
        id+=1
        output.append(car_data)
    conn.close()
    return output
for i in range(len(postgre())):
    users.append(postgre()[i])

print(users)
@app.route("/api/users")
def get_users():
    return jsonify(users)

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
