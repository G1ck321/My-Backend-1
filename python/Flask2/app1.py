from flask import Flask, jsonify, send_from_directory,render_template
import json
from flask import request
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5001","http://127.0.0.1:5000"])#from,to
#CORS(app, origins=["current port or domain", "port that wants to receive"])

#this is flask code to receieve data from an index.html
#This data will update the users list
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
    },


]



#handle options preflight request
#not advised security risk allows any website to make requests to your api
# @app.after_request
# def after(response):
# response.headers.add('Acess-Control-Allow-Origin','*')
# response.headers.add('Acess-Control-Allow-Headers','Content-Type,Authorization')
# response.headers.add('Acess-Control-Allow-Methods','GET,PUT,POST,DELETE,OPTIONS')
# return response


@app.route("/api/users",methods=['GET','POST','PUT','DELETE'])
def create_users():
    #validate input
    if request.method=="POST":
        
        data = request.get_json()
        if not all(key in data for key in ['username','age','job']):
            #ensures all the fields are sent if there are less than 3 keys in data all be false
            return{"error:missing required fields"},400
        #duplicates
        for user in users:
            for user_data in user:
                if data["username"] == user_data[0]:
                    return jsonify({"error":"Username already exists"})
        new_id = len(users)+1
        new_user = "user"+str(new_id)
        data.update({"id":new_user})
        users.append(data)
        return jsonify({"message": "User added successfully","users":users[-1]}),201
    if request.method =="GET":
        return jsonify(users),200
    
#flawed logic
# def get_users():
# if request.method == 'POST':
# data = request.get_json()
# list_data = list(data.values())#was a dict
# for user_key, user_value in users[-1].items():
# #gets "users" text
# user_dict = {}

# print(int(user_key[-1])+1)#removes the number from users
# for i,p in enumerate(users):
# print(users[i].get("user"+str(i+1)))#gets the value of each user +1 is because i=0
# if list_data[0] in users[i].get("user"+str(i+1)) or users[i]!=users[-1]:
# continue


# elif list_data[1] not in users[i].get("user"+str(i+1)) and users[i]==users[-1]:
# user_dict["user"+f'{(int(user_key[-1])+1)}'] = list_data
# users.append(user_dict)
# return jsonify({"message": "User added successfully", "users": users[-1]}), 201

# else:
# return jsonify({"message": "Username already exists"}), 200
# return jsonify({"message": "Username already exists"}), 200
# print(users)
# if request.method =='GET':
# return jsonify(users),200

@app.route("/")
def serve():
# return send_from_directory('.', 'index.html')
    return render_template('index.html')
# @app.route("/")
# def home():
# return jsonify(users)

@app.route("/update")
def update_user():
    return render_template('update.html')

@app.route("/api/users/<username>",methods = ['PUT','GET'])
def update_users(username):

    data = request.get_json()
    if request.method == 'PUT':
        # users[0]["username"] = data["username"].title()
        # users[0]["age"] = data["age"]
        # users[0]["job"] = data["job"].title()
        for user in users:
            if user["username"] == username:
                user["age"] = data["age"]
                user["job"] = data["job"].title()
                

    return jsonify({"Success":"You have updated your details"})

if __name__ == "__main__":
    app.run(port=5001, debug=True)