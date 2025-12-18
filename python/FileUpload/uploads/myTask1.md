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

This is a great pivot. Switching to **PostgreSQL** and **Flask-SQLAlchemy** immediately makes your learning professional-grade. This is exactly what you will use in a real job.

Here is your complete resource package for Days 1 & 2, updated for a real database workflow.

### 1\. The Best Practical YouTube Videos

Since you are adding SQLAlchemy, you need to see how the database connects to the auth system.

**For Day 1 (Hashing & Database Setup):**

  * **Channel:** Pretty Printed
      * **Video:** "Intro to Flask-SQLAlchemy" (Watch first to understand the DB connection).
      * **Video:** "Password Authentication with Flask-Login" (Only watch the *Hashing* part, ignore the `UserMixin` stuff for now since we are doing JWTs).
  * **Channel:** Corey Schafer
      * **Video:** "Python Flask Tutorial: Full-Featured Web App Part 4 - Database with Flask-SQLAlchemy".
      * **Why:** He shows you exactly how to create the `User` class and table.

**For Day 2 (JWTs & Protection):**

  * **Channel:** Pretty Printed
      * **Video:** "How to use Flask-JWT-Extended".
      * **Why:** This is the definitive guide. He walks through exactly the code structure we are using below.
  * **Channel:** Tech With Tim
      * **Video:** "Flask REST API Tutorial - Authentication".
      * **Why:** Good for seeing a broad overview of how an API handles tokens.

-----

### 2\. Day 2 Teaching: The JWT Analogy

**The Concept:**
Day 1 was about the **Key** (Password). Day 2 is about the **Wristband** (JWT).

**The Analogy: The Nightclub**

1.  **Login (The Bouncer):** You walk up to the club and show your ID (Username/Password). The bouncer checks his list (Database). If you are on it, he doesn't ask you to show your ID every time you buy a drink.
2.  **The Token (The Wristband):** Instead, he stamps your hand or gives you a specific colored **wristband**.
3.  **Access (The Bartender):** When you go to the bar (Protected Route), you just show your wristband. The bartender doesn't care who you are or what your password is; they only care that the wristband is **valid** and **hasn't been tampered with**.

**Why JWT?**
If you have 1,000,000 users, checking the database for a password on *every single click* is slow. Checking a mathematical signature on a wristband (JWT) is instant and doesn't require a database lookup.

-----

### 3\. The Full Code (Day 1 + Day 2 + PostgreSQL)

This script combines **Hashing** (Day 1), **JWTs** (Day 2), and **SQLAlchemy** (Database).

**Prerequisites:**
Run this in your terminal:

```bash
pip install flask flask-sqlalchemy flask-jwt-extended psycopg2-binary
```

*Note: Make sure you have a PostgreSQL database named `auth_db` created locally.*

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURATION ---
# 1. Point to your PostgreSQL Database
# Format: postgresql://username:password@localhost/database_name
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Secret Key for signing the JWT (The "stamp" only you own)
app.config['JWT_SECRET_KEY'] = 'super-secret-key-change-this-in-production'

# Initialize Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- DATABASE MODEL ---
# This defines what the "users" table looks like in Postgres
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Storing the HASH, not the password
    role = db.Column(db.String(20), default='user') # For your future admin tasks

# Create tables (Run this once)
with app.app_context():
    db.create_all()

# --- ROUTES ---

# 1. SIGNUP (The "Registration Desk")
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Check if user exists
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "User already exists"}), 409

    # Day 1 Skill: Hash the password!
    hashed_pw = generate_password_hash(password)

    # Save to Postgres
    new_user = User(username=username, password_hash=hashed_pw, role="admin")
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created"}), 201

# 2. LOGIN (The "Bouncer")
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Find user in DB
    user = User.query.filter_by(username=username).first()

    # Verify user exists AND password matches hash
    if user and check_password_hash(user.password_hash, password):
        # Day 2 Skill: Create the Wristband (JWT)
        # We put the 'id' and 'role' inside the token so we know who they are later
        access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Bad username or password"}), 401

# 3. PROTECTED ROUTE (The "VIP Lounge")
@app.route('/admin-dashboard', methods=['GET'])
@jwt_required() # <--- The Guard: Rejects request if token is missing/invalid
def admin_dashboard():
    # Who is this? Get the ID from the token
    current_user_id = get_jwt_identity()
    
    # Optional: Fetch fresh data from DB if needed
    user = User.query.get(current_user_id)
    
    return jsonify({
        "msg": f"Welcome back, {user.username}", 
        "secret_data": "Here is the sales report..."
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
```

-----

### 4\. What to Build & Practice (Day 1 + Day 2)

Don't just run the code above. You need to break it and rebuild it to learn.

**Practice Project: "The Private Diary"**
Build a simple API where users can sign up and post private notes that *only they* can see.

**Step-by-Step Build:**

1.  **Modify the Model:** Add a second table called `Note` in SQLAlchemy.
      * Columns: `id`, `content`, `user_id` (ForeignKey linking to User).
2.  **The Relationship:** Use `db.relationship` to link Users to Notes.
3.  **The Protected POST:** Create a route `/add-note`.
      * User sends `{"content": "I ate pizza today"}`.
      * You use `get_jwt_identity()` to find out *who* sent it.
      * You save the note with that user's ID.
4.  **The Protected GET:** Create a route `/my-notes`.
      * Use `get_jwt_identity()` again.
      * Query the database: `Note.query.filter_by(user_id=current_user_id).all()`.
      * Return only that user's notes.

**Why this helps:**
This teaches you the most critical part of JWTs: **Identity**. It's not just about letting people in; it's about knowing *which* data belongs to *which* token.

**Tip for Success:**
When you get stuck on the database relationship part (connecting Users to Notes), search for "Flask-SQLAlchemy One to Many Relationship" on YouTube. Corey Schafer has a perfect video on this.

Welcome to **Day 3: Role-Based Access Control (RBAC) & Custom Decorators.**

You have a working login system (Day 1 & 2). Users can get a token (wristband) and enter the club.
**The Problem:** Right now, *anyone* with a token can access the "Admin Dashboard" if they know the URL. The janitor shouldn't have access to the CEO's safe, even if they both work in the same building.

**The Goal:** We will build a specific lock that only opens for users where `role = 'admin'`.

-----

### Part 1: The Analogy (The Keycard Color)

1.  **Authentication (Day 1 & 2):** The Security Guard checks your ID and gives you a **Keycard**. This gets you through the front door.
2.  **Authorization (Day 3):** You try to enter the "Server Room."
      * The card reader checks the **Color** of your Keycard.
      * **Blue (User):** Access Denied.
      * **Red (Admin):** Access Granted.

In code, we do this using a **Custom Decorator**. You've used `@app.route` and `@jwt_required`. Now, you will write your own: `@admin_required`.

-----

### Part 2: The "Secret Sauce" (Python Decorators)

A decorator is a function that wraps around another function to change its behavior.

We need to create a wrapper that runs **after** `@jwt_required` but **before** the actual function (`admin_dashboard`).

  * *Step 1:* Check JWT. (Is the user logged in?)
  * *Step 2:* **Custom Check.** (Does the token say "admin"?)
  * *Step 3:* Run the function.

-----

### Part 3: The Code (Full Implementation)

We are building upon the Day 2 code. I have highlighted the **new** sections.

**Prerequisites:**
No new installs needed. We are using standard Python libraries (`functools`) alongside `flask-jwt-extended`.

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps  # <--- NEW: Required for creating decorators

app = Flask(__name__)

# --- CONFIGURATION (Same as Day 2) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- DATABASE MODEL ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # This column is the star of today's show
    role = db.Column(db.String(20), default='user') 

# --- NEW: CUSTOM ERROR HANDLING ---
# This makes your API look professional. Instead of crashing or generic HTML,
# it gives clean JSON when tokens are invalid.
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Signature verification failed", "error": "invalid_token"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"message": "Request does not contain an access token", "error": "authorization_required"}), 401

# --- NEW: THE @admin_required DECORATOR ---
# This is the code you will eventually give to your CRUD team.
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 1. verify_jwt_in_request() ensures the token is valid 
            # (We don't need @jwt_required on the route if we put this here)
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            
            # 2. Get the claims inside the JWT
            claims = get_jwt()
            
            # 3. Check if the 'role' claim is 'admin'
            if claims.get("role") == "admin":
                return fn(*args, **kwargs) # Success! Run the original function
            else:
                return jsonify(msg="Admins only!"), 403 # 403 = Forbidden
        return decorator
    return wrapper

# --- ROUTES ---

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    # For testing, let's allow setting the role in the signup
    # IN REAL LIFE: You would force this to be 'user' and change it manually in DB
    role = data.get('role', 'user') 
    
    hashed_pw = generate_password_hash(data.get('password'))
    new_user = User(username=data.get('username'), password_hash=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if user and check_password_hash(user.password_hash, data.get('password')):
        # CRITICAL: We bake the role INTO the token here.
        # This means we don't need to query the DB every time they visit a page.
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Bad credentials"}), 401

# --- THE PROTECTED ROUTES ---

# 1. Route for ANY logged-in user
@app.route('/general-dashboard', methods=['GET'])
@jwt_required()
def general_dashboard():
    return jsonify(msg="Welcome, employee!"), 200

# 2. Route for ADMINS ONLY
@app.route('/admin-dashboard', methods=['GET'])
@admin_required() # <--- Our custom guard logic runs here
def admin_dashboard():
    return jsonify(msg="Welcome, Boss! Here are the nuclear codes."), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```

-----

### Part 4: Testing (The Lab)

You need to prove that a normal user gets blocked, but an admin gets in.

**1. Create a "Regular" User**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username": "employee", "password": "123", "role": "user"}' http://127.0.0.1:5000/signup
```

**2. Create an "Admin" User**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username": "boss", "password": "123", "role": "admin"}' http://127.0.0.1:5000/signup
```

**3. Login as Employee (Get Token A)**

  * Copy the token returned.
  * Try to access `/admin-dashboard`.
  * **Result:** `{"msg": "Admins only!"}` (Status 403).

**4. Login as Boss (Get Token B)**

  * Copy the token returned.
  * Try to access `/admin-dashboard`.
  * **Result:** `{"msg": "Welcome, Boss!..."}` (Status 200).

-----

### Part 5: Resources for Day 3

**1. Video: Understanding Decorators**
This is the hardest Python concept so far. You need to understand `*args` and `**kwargs`.

  * **Channel:** Corey Schafer
  * **Video:** "Python Tutorial: Decorators - Dynamically Alter The Functionality Of Your Functions"
  * *Why:* He explains exactly what that `@wraps` code is doing.

**2. Video: Claims in JWT**

  * **Channel:** Pretty Printed
  * **Video:** "Storing Custom Data in the JWT with Flask-JWT-Extended"
  * *Why:* This explains `additional_claims`, which is how we put the "role" inside the token so we don't have to query the database on every request.

-----

### Day 3 Project: "The Promotion System"

**Goal:** Create a system where one Admin can promote another user to Admin.

**Task:**

1.  Create a route `/promote/<int:user_id>` (Method: PUT).
2.  Protect it with `@admin_required`. (Only admins can promote people).
3.  Inside the function:
      * Query the database for the `user_id`.
      * Change their `role` to "admin".
      * Commit to database.
4.  **Test:**
      * Log in as "Boss".
      * Promote "Employee".
      * Log "Employee" out and back in (to get a new token with the new role).
      * Check if "Employee" can now access the Admin Dashboard.

**Tip:**
This project proves you understand **Authorization** (Who can do what) and **State Change** (Updating the DB securely).

Yes, exactly\! **SQLite is built into Python**, so you do not need to install any extra database software (like PostgreSQL) or drivers (like `psycopg2`) right now. It creates a simple file on your computer (e.g., `instance/project.db`) that acts as your database.

This is the perfect way to start. Because we are using **Flask-SQLAlchemy**, switching to PostgreSQL later is as easy as changing **one line of code** (the configuration URL). The rest of your Python code remains exactly the same.

Here is your complete **Day 1 & 2 Code** adapted for SQLite, with rich comments explaining every part.

### Phase 1: Setup & Basic Auth (Day 1 & 2)

**Goal:** Signup, Login, Hashing, and JWT Generation using SQLite.

**Prerequisites:**
You only need these libraries now:

```bash
pip install flask flask-sqlalchemy flask-jwt-extended
```

**The Code (`app.py`):**

```python
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURATION ---

# 1. DATABASE CONFIGURATION (SQLite)
# valid SQLite URL: sqlite:///project.db
# This will create a file named 'project.db' in an 'instance' folder in your project directory.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'project.db')

# This suppresses a warning from SQLAlchemy that we don't need to worry about
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. SECURITY CONFIGURATION
# This key is used to sign the JWTs. If a hacker gets this, they can forge tokens.
app.config['JWT_SECRET_KEY'] = 'dev-secret-key-change-this-later' 

# Initialize Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- DATABASE MODEL ---
# This class defines your table structure.
# SQLAlchemy translates this Python class into SQL commands (CREATE TABLE...) automatically.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Unique ID for every user (1, 2, 3...)
    username = db.Column(db.String(50), unique=True, nullable=False) # Must be unique
    password_hash = db.Column(db.String(128), nullable=False) # Long string to hold the hash
    role = db.Column(db.String(20), default='user') # 'user' or 'admin'

# --- HELPER FUNCTION TO SETUP DB ---
# In a real app, you might use Flask-Migrate, but this is perfect for learning.
# Run this file once to create the database file!
with app.app_context():
    db.create_all()

# --- ROUTES ---

# 1. SIGNUP
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user') # Default to 'user' if not provided

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 409

    # HASHING (The "Blender")
    # Never store the raw password!
    hashed_pw = generate_password_hash(password)

    # Create new User object and save to SQLite
    new_user = User(username=username, password_hash=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit() # This saves the changes to the 'project.db' file

    return jsonify({"msg": "User created successfully"}), 201

# 2. LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Look up user in SQLite
    user = User.query.filter_by(username=username).first()

    # Verify Password
    if user and check_password_hash(user.password_hash, password):
        # Create the JWT (The "Wristband")
        # We allow the token to store the user's ID and Role.
        # This is useful so we don't have to query the DB on every request.
        access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Invalid username or password"}), 401

# 3. PROTECTED ROUTE
@app.route('/my-profile', methods=['GET'])
@jwt_required() # <--- This protects the route!
def my_profile():
    # Who is accessing this?
    current_user_id = get_jwt_identity()
    
    # Fetch their details from DB
    user = User.query.get(current_user_id)
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "msg": "You are seeing this because you have a valid token!"
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
```

-----

### Phase 2: Role-Based Access (Day 3)

**Goal:** Adding the Custom Decorator (`@admin_required`) using SQLite.

This code is an **add-on** to the code above. You can add these imports and functions to the same file.

**Imports to add:**

```python
from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request
```

**The Custom Decorator Code:**

```python
# --- CUSTOM DECORATOR ---
# Copy-paste this helper function. It checks if the user is an admin.
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 1. Verify the JWT is valid and present
            verify_jwt_in_request()
            
            # 2. Get the "claims" (the data inside the token)
            claims = get_jwt()
            
            # 3. Check the role
            if claims.get("role") == "admin":
                return fn(*args, **kwargs) # Pass! Execute the function
            else:
                return jsonify(msg="Admins only! Access Forbidden."), 403 # Fail!
        return decorator
    return wrapper

# --- ADMIN ONLY ROUTE ---
@app.route('/admin-dashboard', methods=['GET'])
@admin_required() # <--- Use your new custom decorator here
def admin_dashboard():
    return jsonify(msg="Welcome to the secret admin panel!"), 200
```

-----

### Future-Proofing: How to Migrate Later

When your Project Manager says "Okay, we are deploying to production now, switch to Postgres," here is exactly what you will do:

1.  **Install the driver:**
    `pip install psycopg2-binary`

2.  **Change ONE line in config:**

    *Change this:*

    ```python
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
    ```

    *To this:*

    ```python
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'
    ```

That is the beauty of **SQLAlchemy** (the ORM). It translates your Python code into SQLite SQL today, and PostgreSQL SQL tomorrow, without you having to rewrite your logic.