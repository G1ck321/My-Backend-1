from flask import Flask, jsonify, request,render_template
from config import app
from model import get_all_todos, create_todo, get_todo, delete_todo, update_todo, signIn
#pip install --force-reinstall supabase FIx conflicts


signIn()

if __name__ == "__main__":
    app.run( port=5000, debug=True)