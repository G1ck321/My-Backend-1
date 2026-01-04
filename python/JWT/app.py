from flask import Flask, jsonify, request, make_response
from flask import render_template, session
import jwt
from datetime import datetime, timedelta
from functools import wraps 

app = Flask(__name__)
# SECRET KEY is with underscore
app.config['SECRET_KEY'] = 'U_Hq29Q6m_-bUJcuTMaI'
app.permanent_session_lifetime = timedelta(seconds=240)
#first method import; os.urandom(num of char)
#import uuid; uuid.uiud4().hex gives different every single time
#import secrets(py-3.6) secrets.token_urlsafe(12)
def tokenRequired(func):
    #returns a decorater that invokes a method called update_wrapper()
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        # 2) Call the protected route with the token (as query param, per your current code)
        # curl "http://localhost:5000/auth?token=<JWT_STRING>"
        if not token:
            return jsonify({"Alert":"token is missing."})
            print(token,"tok")
        #jwt allows you store on the client
        try:
            #mordern versions require you specify 
            payload = jwt.decode(token, app.config["SECRET_KEY"],
            options={"require": ["exp"]})
        # If exp is in the payload, PyJWT will raise ExpiredSignatureError after it passes
        except jwt.ExpiredSignatureError: 
            return jsonify({"Alert": "Token expired"}), 401 
        except jwt.InvalidTokenError: 
            return jsonify({"Alert": "Invalid Token!"}), 401
        return func(*args, **kwargs)#call original function
    return decorated
@app.route('/public')
def public():
    return 'For Public'

@app.route('/auth')
@tokenRequired
def auth():
    return 'JWT is verified welcome to dashboard'

@app.route("/")
def home():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        
        return 'Logged in currently!'
@app.route("/login",methods=['POST'])
def login():
    if request.form["username"] and request.form["password"] =='123456':
        session.permanent = True
        
        session["logged_in"] = True
        token = jwt.encode({
            'user' : request.form["username"],
            #exp not expiration
            'exp':str(datetime.utcnow()+timedelta(seconds=240))
        },
        app.config['SECRET_KEY'])
        print(token,"tok2")
        
        # return jsonify({'token':token.decode('utf-8')}),201
        
        return jsonify({'token':token}),201
    else:
        return make_response("Unable to verify",403,{"WWW-Authenticate":'Basic realm : "Authenticaion Failed!"'})
@app.post("/logout") 
def logout(): 
    session.pop("logged_in", None) 
    return jsonify({"message": "logged out"})
if __name__ == "__main__":
    app.run(debug=True)
