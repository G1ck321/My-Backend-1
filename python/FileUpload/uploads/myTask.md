Here is your comprehensive Guide for Day 1: The Foundation of Authentication (Password Hashing).
Today, we are not issuing tokens yet. We are building the steel door that protects the house. If this part is weak, the best locks (JWTs) in the world won't matter.
Part 1: The Concepts (No Code Yet)
Before we type a single line, you must understand Hashing and Salting.
1. The Problem: Plain Text
Imagine you store your admin passwords in a database like this:
User: "Admin" | Password: "monkey123"
If a hacker breaks into your database (SQL Injection, leaked backup, etc.), they can read "monkey123" and immediately log in. This is a catastrophic failure.
2. The Solution: Hashing (The "One-Way Street")
Hashing is a mathematical function that turns data (a password) into a scrambled string of characters (a hash).
The Golden Rule: Hashing is one-way.
 * Encryption is like a suitcase with a key. You can lock it (encrypt) and unlock it (decrypt) if you have the key.
 * Hashing is like a Blender. You put a banana in and blend it. You cannot reverse the process to get the banana back.
When a user logs in, you don't "decrypt" the stored password. instead, you take the password they just typed, blend it again, and see if the resulting smoothie matches the smoothie you have in the fridge (the database).
3. The Enhancement: Salting (The "Unique Spice")
If two users both have the password "password123", their hashes would look exactly the same. A hacker could use a "Rainbow Table" (a giant list of pre-calculated hashes) to reverse them instantly.
The Fix: We add a Salt.
A salt is a random string added to the password before it goes into the blender.
 * User A: "password123" + "salt_A" -> Hash_A
 * User B: "password123" + "salt_B" -> Hash_B
Now, even though they have the same password, the database stores completely different strings.
Part 2: The Tools
We will use werkzeug.security.
It comes installed with Flask and handles the complex math (algorithms like scrypt or pbkdf2) and automatic salting for you.
You will use exactly two functions:
 * generate_password_hash(password): Turns "monkey123" into scrypt:32768:8:1$kPv...
 * check_password_hash(hash, password): Takes the stored hash and the guess, and returns True or False.
Part 3: The Project (Admin Signup & Verification)
We will build a simple API with two routes:
 * POST /signup: Accepts a username/password, hashes it, and saves it.
 * POST /login: Accepts a username/password and checks if they match.
Step 1: File Setup
Create a file named day1_auth.py.
Prerequisite: Ensure you have Flask installed (pip install flask).
Step 2: The Full Code
Copy this into your file. I have commented every logical step.
from flask import Flask, request, jsonify
# Werkzeug is the toolkit under Flask's hood that handles security
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- MOCK DATABASE ---
# In a real app, this would be a SQL table or MongoDB collection.
# We are using a Python dictionary to simulate a database for learning purposes.
# Structure: { "username": { "password": "hashed_string", "email": "..." } }
users_db = {}

# ==========================================
# 1. ADMIN SIGNUP ROUTE
# Goal: Receive a raw password, crush it (hash), and store the debris.
# ==========================================
@app.route('/signup', methods=['POST'])
def signup():
    # Get JSON data from the request
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')

    # Basic Validation: Ensure both fields are sent
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if user already exists
    if username in users_db:
        return jsonify({"error": "User already exists"}), 409 # 409 = Conflict

    # --- THE MAGIC MOMENT: HASHING ---
    # method='pbkdf2:sha256' is a standard, secure algorithm.
    # Flask does the Salting automatically behind the scenes here!
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # Store the user in our mock database
    # NOTICE: We store 'hashed_password', NEVER the raw 'password'
    users_db[username] = {
        "password": hashed_password,
        "role": "admin" # We will use this in Week 2
    }

    # Print to console so you can see what the hash looks like (Learning only!)
    print(f"DEBUG: Stored user '{username}' with hash: {hashed_password}")

    return jsonify({"message": "Admin registered successfully!"}), 201


# ==========================================
# 2. ADMIN LOGIN (VERIFICATION) ROUTE
# Goal: Check if the password provided matches the hash in the DB.
# ==========================================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 1. Check if user exists in our DB
    if username not in users_db:
        return jsonify({"error": "Invalid username or password"}), 401

    # 2. Retrieve the user dictionary
    user_record = users_db[username]
    stored_hash = user_record['password']

    # 3. VERIFY THE PASSWORD
    # check_password_hash(stored_hash, user_input)
    # This re-hashes the input using the SAME salt found in the stored_hash
    # and compares the results.
    is_valid = check_password_hash(stored_hash, password)

    if is_valid:
        # Success! (In Day 2, we will return a JWT token here)
        return jsonify({"message": "Login Successful. Welcome Admin!"}), 200
    else:
        # Failure
        return jsonify({"error": "Invalid username or password"}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000)

Part 4: How to Test This (The "Lab Work")
Run your app: python day1_auth.py.
Open a separate terminal to run these curl commands (or use Postman).
Test 1: Register a new Admin
We will send a password "secure123". Watch your Python console output to see the hash.
Request:
curl -X POST -H "Content-Type: application/json" -d '{"username": "admin1", "password": "secure123"}' http://127.0.0.1:5000/signup

Expected Output (Client):
{"message": "Admin registered successfully!"}

Look at your Python Console:
You will see something like:
DEBUG: Stored user 'admin1' with hash: pbkdf2:sha256:600000$....long_random_string...
Notice: The hash is much longer than the password and looks like gibberish. This is good.
Test 2: Log in with CORRECT password
Request:
curl -X POST -H "Content-Type: application/json" -d '{"username": "admin1", "password": "secure123"}' http://127.0.0.1:5000/login

Expected Output:
{"message": "Login Successful. Welcome Admin!"}
Test 3: Log in with WRONG password
Request:
curl -X POST -H "Content-Type: application/json" -d '{"username": "admin1", "password": "wrongpassword"}' http://127.0.0.1:5000/login

Expected Output:
{"error": "Invalid username or password"}
Deep Dive: What just happened inside check_password_hash?
When you ran Test 2, check_password_hash performed a forensic investigation:
 * Extraction: It looked at the stored string: pbkdf2:sha256:600000$AbCdEf...$12345....
 * Analysis: It read the metadata inside that string:
   * "Ah, this was hashed using pbkdf2:sha256."
   * "The salt used was AbCdEf...."
 * Replication: It took your input "secure123", added the salt AbCdEf..., and ran the pbkdf2 algorithm exactly 600,000 times (the work factor).
 * Comparison: It produced a result. It compared that result to the end of the stored string (12345...). They matched, so it returned True.
Assignment for Tomorrow
 * Run this code locally.
 * Try to sign up two different users with the exact same password.
 * Print the users_db dictionary. Observe that their hashes are different. This proves that werkzeug is automatically salting them for you.
Once you understand this "One-way Blender" concept, you are ready for Day 2: The JWT Token.
------------------------------------------
Here is the breakdown. I will clear up the os confusion first, separate the days, and then give you a deep dive into Day 4 and Day 5.
Part 1: Why so much os?
You asked about this chunk of code:
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'project.db')

The Problem it Solves:
Computers are stupid about file paths.
 * Windows uses backslashes: C:\Users\You\project\app.py
 * Mac/Linux use forward slashes: /home/you/project/app.py
If you hardcode a path like 'sqlite:///C:/Users/project.db', your code will crash on a Mac.
The os Module Explanation:
 * os.path.dirname(__file__): "Where does this specific python file (app.py) live?"
 * os.path.abspath(...): "Give me the full, absolute address, not just a relative shortcut."
 * os.path.join(basedir, 'project.db'): This is the magic. It intelligently adds the correct slash (\ or /) between the folder path and the filename based on the operating system the code is running on.
In Plain English:
> "Find the folder where this script is running, and put the project.db file right there next to it, regardless of whether I am on Windows or Mac."
> 
Part 2: Day 1 & 2 Separated (SQLite Version)
Here is the clean separation you asked for.
Day 1: The Foundation (Database & Hashing)
Focus: Creating users and securing passwords. No tokens yet.
# day1_hashing.py
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- SQLite Setup ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'day1.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Model ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

with app.app_context():
    db.create_all()

# --- Routes ---
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # 1. Hash the password
    hashed_pw = generate_password_hash(data['password'])
    
    # 2. Save to DB
    new_user = User(username=data['username'], password_hash=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created!"}), 201

@app.route('/login-check', methods=['POST'])
def login_check():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    # 3. Verify Hash
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({"msg": "Password Correct!"}), 200
    
    return jsonify({"msg": "Wrong credentials"}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000)

Day 2: The Access Token (JWT)
Focus: Generating the "wristband" after the password is verified.
# day2_jwt.py
# (Include imports and DB setup from Day 1 above...)
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app.config['JWT_SECRET_KEY'] = 'super-secret-key' # CHANGE THIS IN PRODUCTION
jwt = JWTManager(app)

# --- Routes ---
# (Signup is the same as Day 1)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password_hash, data['password']):
        # --- Day 2 Magic: Create Token ---
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Bad credentials"}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify(logged_in_as=current_user_id), 200

Part 3: Day 4 - Expiration & Refreshing (Robustness)
The Concept:
If an Access Token lasts forever, and a hacker steals it, they are logged in as you forever.
To fix this, we use two tokens:
 * Access Token (Short life): Lasts 15 minutes. Used for every API call.
 * Refresh Token (Long life): Lasts 30 days. Used only to get a new Access Token.
The Analogy:
Think of a Secure Office Building.
 * Access Token = Visitor Badge. It allows you to open doors. But it expires automatically at 5:00 PM (Short life).
 * Refresh Token = Your Driver's License. You cannot use your Driver's License to open office doors. But, when your Visitor Badge expires, you go to the front desk, show your Driver's License (Refresh Token), and they print you a new Visitor Badge.
The Code Implementation:
# day4_refresh.py
from datetime import timedelta
from flask import Flask, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity
)

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'

# --- CONFIGURING EXPIRATION ---
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15) # Short Life
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)   # Long Life

jwt = JWTManager(app)

# --- CLEAN ERROR HANDLING (Task from your list) ---
# This ensures the frontend gets clean JSON, not HTML errors
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "token_expired", "msg": "Token has expired"}), 401

@jwt.invalid_token_loader
def my_invalid_token_callback(error):
    return jsonify({"error": "invalid_token", "msg": "Signature verification failed"}), 401

@app.route('/login', methods=['POST'])
def login():
    # ... (assume user/password verification passed) ...
    user_id = 1 
    
    # Create BOTH tokens
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    
    return jsonify({
        "access_token": access_token, 
        "refresh_token": refresh_token
    }), 200

# --- THE REFRESH ROUTE ---
# The frontend calls this when the Access Token dies (401 Error)
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # <--- Only accepts Refresh Tokens!
def refresh():
    # Who is this user?
    current_user = get_jwt_identity()
    
    # Grant a NEW access token
    new_access_token = create_access_token(identity=current_user)
    
    return jsonify(access_token=new_access_token), 200

Part 4: Day 5 - Logout & Blocklisting (Security)
The Concept:
A JWT is valid until it expires. You cannot "delete" it from the server because the server doesn't store it (that's the point of JWTs).
So, how do we "Log Out"? We create a Blocklist (also called a Blacklist or Revocation List).
The Analogy:
The "Do Not Serve" List at a bar.
The bartender doesn't take your ID away when you leave. But if you get kicked out (Logout), the bouncer writes your name on a clipboard.
Every time someone orders a drink, the bartender checks the clipboard: "Is this person banned?"
 * If yes -> Deny service.
 * If no -> Pour drink.
The Code Implementation:
We need a new database table to store the IDs of revoked tokens.
# day5_blocklist.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt, create_access_token
)

app = Flask(__name__)
# ... (DB Config from Day 1) ...
db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- 1. THE BLOCKLIST MODEL ---
class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True) # JWT ID
    created_at = db.Column(db.DateTime, nullable=False)

# --- 2. THE CHECKER (The Bartender) ---
# This runs on EVERY @jwt_required request
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"] # Extract the unique ID of the token
    
    # Query DB: Is this token in the blocklist?
    token = TokenBlocklist.query.filter_by(jti=jti).first()
    
    # If token is found, return True (Yes, it is revoked)
    return token is not None 

# --- 3. THE LOGOUT ROUTE ---
@app.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    # Get the unique ID (JTI) of the token currently being used
    jti = get_jwt()["jti"]
    
    # Add it to the Blocklist DB
    # We use 'datetime.utcnow()' (ensure you import datetime)
    from datetime import datetime
    now = datetime.utcnow()
    
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()
    
    return jsonify(msg="Access token revoked. Logged out."), 200

Summary of Your Learning Curve
 * Day 1: You learned how to verify passwords without storing them (Hashing).
 * Day 2: You learned how to issue a "wristband" (JWT) so users stay logged in.
 * Day 3: You learned how to separate "Admins" from "Users" (RBAC).
 * Day 4: You learned that wristbands must expire (Refresh Tokens) for safety.
 * Day 5: You learned how to kick people out by writing their wristband ID on a banned list (Blocklisting).
This is the complete lifecycle of a professional authentication system. You are ready to build this!
