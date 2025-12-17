from config import supabase, tablename
from datetime import timedelta, datetime
def signIn():
    users_email:str = "agbejimigbemiga@gmail.com"
    users_password:str = "postman456"
    user = supabase.auth.sign_up({ "email": users_email, "password": users_password })
def get_all_todos():
    "Reads all tasks from todo table"
    response = supabase.from_(tablename).select("*").execute()
    return response.data
def get_todo(id):
    "Get a specific todo"
    todo = supabase.table(tablename).select("id","name").eq("id",id).execute()
    return todo.data
def create_todo(new_todo):
    """Inserts new task in ToDo table"""
    
    response = supabase.table(tablename).insert(new_todo).execute()
    return response.data
    
def delete_todo(id):
    "Deleet a specific todo"
    response = supabase.table(tablename).delete().eq("id",id).execute()
    #id and create at are automatically generted
    return response.data
def update_todo(id, new_todo):
    """Updates a todo"""
    response = supabase.table(tablename).update(new_todo).eq("id",int(id)).execute()
    # print("Supabase update response:", response.data, response.error)
    return response.data