from flask import Flask, jsonify, request,render_template
from config import app
from model import get_all_todos, create_todo, get_todo, delete_todo, update_todo, signIn
#pip install --force-reinstall supabase FIx conflicts


signIn()
@app.route("/login")
def login():
    return render_template("index.html")

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
    return jsonify(todo),200

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
    
if __name__ == "__main__":
    app.run( port=5000, debug=True)