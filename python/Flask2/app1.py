from flask import Flask, jsonify, send_from_directory,render_template
import json
from flask import request
from flask_cors import CORS
from config import app,db
from model import User
from flask_migrate import Migrate
from sqlalchemy.exc import NoResultFound

with app.app_context():
    # db.init_app(app)
    #binds the sqlalchemy to app
    
    db.create_all()
    
CORS(app, origins=["http://127.0.0.1:5001","http://127.0.0.1:5000"])#from,to
#CORS(app, origins=["current port or domain", "port that wants to receive"])

#this is flask code to receieve data from an index.html
#This data will update the users list
migrate = Migrate()
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

migrate.init_app(app,db)
@app.route("/api/users",methods=['GET','POST','PUT','DELETE'])
def create_users():
    #validate input
    if request.method=="POST":
        data = request.get_json()
        
        if not all(key in data for key in ['username','age','job']):
            #ensures all the fields are sent if there are less than 3 keys in data all be false
            return{"error:missing required fields"},400
        age = data["age"]
        job = data["job"]
        username = data["username"]
        new_user = User(age=age, job=job, username=username)
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
        # if any error it catches it
            db.session.rollback()
            print("Database error:", str(e))
            return (jsonify({"message": str(e)}), 400)
        return jsonify({"message": "User added successfully","users":users[-1]}),201
    
    #     #duplicates
    #     for user in users:
    #         for user_data in user:
    #             if data["username"] == user_data[0]:
    #                 return jsonify({"error":"Username already exists"})
    #     new_id = len(users)+1
    #     new_user = "user"+str(new_id)
    #     data.update({"id":new_user})
    #     users.append(data)
    if request.method =="GET":
        try:
            user = User.query.all()
            json_users = list(map(lambda x: x.to_json(),user))
            return jsonify(json_users),200
        except Exception as e:
        # if any error it catches it
            db.session.rollback()
            print("Database error:", str(e))
            return (jsonify({"message": str(e)}), 400)
        
    
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

@app.route("/api/users/<username>",methods = ['PUT','GET', 'DELETE'])
def update_users(username):

    if request.method == 'PUT':
        data = request.get_json()
        # users[0]["username"] = data["username"].title()
        # users[0]["age"] = data["age"]
        # users[0]["job"] = data["job"].title()
        age = data["age"]
        job = data["job"].title()
        try:
            
            User.query.filter_by(username=username).update({"age":age, "job":job})
            db.session.commit()
        except Exception as e:
        # if any error it catches it
            db.session.rollback()
            print("Database error:", str(e))
            return (jsonify({"message": str(e)}), 400)
        return jsonify("User successfully updated"),200
    if request.method == "GET":
        # user = User.query.get(username)
        try:
            #list objects .all(), .first() actual str or int
            
            # user = db.session.get(User, username)
            user = db.session.scalar(db.select(User).where(User.username==username))
            this_user = {"age":user.age, "id":user.id,"job":user.job,"username": username}
            return jsonify(this_user),200
            if user is None:
                raise NoResultFound(f"User with username {username} not found.")
            # if type(int(username)) is int:
            # if isinstance(int(username), int) :
                #checks whether the value is an integer or a subclass of int
                #like bool, it inherits from int
            # user = User.query.filter(User.username.ilike(f'%{username}%')).first()
        
            
        except Exception as e:
        # if any error it catches it
            db.session.rollback()
            print("Database error:", str(e))
            return (jsonify({"message": str(e)}), 400)
    if request.method == "DELETE":
        try:
            User.query.filter_by(username = username).delete()
            db.session.commit()
            return jsonify("Done"),204
        except Exception as e:
        # if any error it catches it
            db.session.rollback()
            print("Database error:", str(e))
            return (jsonify({"message": str(e)}), 400)
        


    

@app.route("/api/migrate", methods=["GET"])
def getAll():
    # users = User.query.all()
    stmt = db.select(User).order_by(User.username)
    user = db.session().scalars(stmt).all()
    print(type(user))
    json_users = list(map(lambda x:x.to_json(), user))
    print(type(json_users))
    return jsonify(json_users),200




if __name__ == "__main__":
    app.run(port=5001, debug=True)