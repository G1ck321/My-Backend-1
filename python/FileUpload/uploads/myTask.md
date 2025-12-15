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
