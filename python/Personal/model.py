from config import supabase

def get_all_todos():
    "Reads all tasks from todo table"
    response = supabase.from_("ToDo").select("*").execute()
    return response.data
def create_todo_task():
    """Inserts new task in ToDo table"""
    data = {}
    return response.data