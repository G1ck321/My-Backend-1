    import os
    from flask import Flask, request, jsonify, render_template
    from flask_sqlalchemy import SQLAlchemy
    from flask_jwt_extended import JWTManager, create_access_token
    from flask_jwt_extended import jwt_required, get_jwt_identity
    from werkzeug.security import generate_password_hash, check_password_hash
    from flask_cors import CORS

    app = Flask(__name__)

    CORS(app)
    #---- Configuration ----
    #1. valid SQLite URL: sqlite:///project.db
    #creates file in an instance folder in your project directory
    basedir = os.path.abspath(os.path.dirname(__file__))

    os.makedirs(basedir+"/instance",exist_ok = True)
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///'+os.path.join(basedir,'instance','project.db')
    #suppresses warnings fro SQLALCHEMy we don't need to worry about
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    #windows uses backslashes \ Mac uses / code will crash on Mac
    # os.path.dirname(__file__): Where does this file(app.py, filename)live
    #os.path.abspath(...)"Absolute address not just a relative shortcut,"
    # os.path.join(basedir,'project.db')adds correct / between

    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column( db.Integer, primary_key = True)
        username = db.Column(db.String(60), unique = True, nullable = False)
        password_hash= db.Column(db.String(128), nullable = False)
        
        def to_json(self):
            """"Allows us convert the fields to JSON
            camelCase is the best for JSON object values use snake_casing"""
            return {
                "id": self.id,
                "username": self.username
                # Do not include password_hash
            }
    with app.app_context():
        db.create_all()
        
    @app.post("/signup")
    def signup():
        data = request.get_json()
        
        hashed_pw = generate_password_hash(data["password"])
        
        new_user  = User(username = data["username"], password_hash = hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg":"User Created!"}),201
    @app.post('/login-check')
    def login_check(): 
        data = request.get_json() 
        user = User.query.filter_by(username = data["username"]).first()
        #Verify Hash
        if user and check_password_hash(user.password_hash, data["password"]):
            return jsonify({"msg":"You have been verified"}), 200
        return jsonify({"msg":"Wrong credentials"}),401

    @app.route("/api/allusers", methods=['GET'])
    def getUsers():
        users = User.query.all()
        secret = User.query.with_entities(User.password_hash).all()
        print(secret)
        json_users = list(map(lambda x: x.to_json(), users))
        
        return jsonify(json_users)

    @app.delete("/api/delete/<int:user_id>")
    def deleteUser(user_id):
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"message":"user not found"})
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"message":"User deleted "})
    #pages
    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/login")
    def login():
        return render_template("login.html")
    if __name__=="__main__":
        app.run(debug=True, port=3500)