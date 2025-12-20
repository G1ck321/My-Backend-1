from config import supabase, tablename
from datetime import timedelta, datetime

def signIn(email, password):
    # Ensure you use .auth. before sign_in_with_password
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return response
    
    
    
def get_all_todos():
    "Reads all tasks from todo table"
    response = supabase.from_(tablename).select("*").execute()
    return response.data
def get_todo(id):
    "Get a specific todo"
    result = supabase.table(tablename).select("id","name").eq("id",id).execute()
    if result.data:
        return result.data[0]  # return dict
    else:
        return None

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
def sign_up_user(email: str, password: str):
    """
    Creates a new user in Supabase Auth.

    Returns a dictionary with user info if successful,
    or None if signup fails.
    """
    if not email or not password:
        return {"error": "Email and password are required"}

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        # Check if user was created successfully
        if response.user:
            return {
                "id": response.user.id,
                "email": response.user.email
            }
        else:
            return {"error": response.get("error", "Signup failed")}

    except Exception as e:
        return {"error": str(e)}
def sign_in_user(email: str, password: str):
    """
    Authenticates a user with Supabase Auth.

    Returns a dict with session info if successful,
    or error message if failed.
    """
    if not email or not password:
        return {"error": "Email and password are required"}

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token if response.session else None
            }
        else:
            return {"error": response.get("error", "Login failed")}

    except Exception as e:
        return {"error": str(e)}