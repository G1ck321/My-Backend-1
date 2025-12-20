from flask import Flask,redirect,url_for, jsonify, request,render_template
from config import app, supabase
from model import get_all_todos, create_todo, get_todo, delete_todo, update_todo, signIn
from model import sign_in_user, sign_up_user
#pip install --force-reinstall supabase FIx conflicts


# user = client.sign_up(email="example@gmail.com", password="*********")

# Sign in with email and password
# user = client.sign_in_with_password(email="example@gmail.com", password="*********")

# Sign in with magic link
# user = client.sign_in_with_otp(email="example@gmail.com")

# Sign in with phone number
# user = client.sign_in_with_otp(phone="+1234567890")

# Sign in with OAuth
# user = client.sign_in_with_oauth(provider="google")
users_email:str = "agbejimigbemiga@gmail.com"
users_password:str = "postman456"
@app.route("/login")
def login():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return "You are logged in!"

@app.route("/reset")
def resetPass():
    return render_template("reset.html")

@app.route("/")
def home():
    return render_template("toDo.html")

@app.get("/api/todo")
def listTodo():
    todos = get_all_todos()
    return jsonify(todos),200

@app.get("/api/user/<int:user_id>")
def getUser(user_id):
    todo = get_todo(user_id)
    if not todo:  # None or empty list
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo[0]), 200  # return the single todo as dict

# @app.route("/auth/callback")
# def auth_callback():
#     # Supabase automatically sets the session in browser storage
#     # We just redirect the user somewhere useful
#     return redirect(url_for("resetPass"))

@app.route("/auth/callback")
def auth_callback():
    return render_template("auth_call.html")

@app.post("/api/newuser")
def createUser():
    new_todo = request.get_json()
    todo = create_todo(new_todo)
    return jsonify (todo),201

@app.delete("/api/delete_todo/<int:user_id>")
def deleteTodo(user_id):
    todo = delete_todo(id = user_id)
    return jsonify(todo),204

@app.patch("/api/update_todo/<int:user_id>")
def updateTodo(user_id):
    data = request.get_json()
    todo = update_todo(id = user_id,new_todo={"name":data["name"]})
    return jsonify(todo),201

    

@app.post("/api/login")
def loginUser():
    data = request.get_json()
    result = sign_in_user(data["email"], data["password"])

    if "error" in result:
        return jsonify(result), 401
    return jsonify(result), 200

@app.post("/api/signup")
def signup():
    data = request.get_json()
    result = sign_up_user(data.get("email"), data.get("password"))

    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201

# @app.route("/reset-password", methods=["GET", "POST"])
# def reset_password():
#     if request.method == "POST":
#         new_password = request.form["password"]

#         supabase.auth.update_user({
#             "password": new_password
#         })


#     return render_template("reset_password.html")


# @app.route("/reset-password", methods=["POST"])
# def reset_password():
#     data = request.get_json()

#     email = data["email"]
#     new_password = data["password"]

#     supabase.auth.update_user({
#         "password": new_password
#     })

#     return redirect(url_for("dashboard"))
#will not work because
# Supabase requires:

# A valid access token

# Belonging to the user

# Created from the email reset link

# Flask does NOT have:

# The user’s access token

# Browser storage

# Email link context

    # return jsonify({"message": "Password updated successfully"})


if __name__ == "__main__":
    app.run( port=5000, debug=True)