from flask import Flask, jsonify, request,render_template
from config import app
from model import get_all_todos, create_todo_task
#pip install --force-reinstall supabase FIx conflicts

users = []

    
@app.route("/login")
def login():
    return render_template("index.html")

@app.route("/")
def home():
    return render_template("toDo.html")

@app.get("/api/todo")
def listTodo():
    todos = get_all_todos()
    return jsonify(todos)
if __name__ == "__main__":
    app.run( port=5000, debug=True)