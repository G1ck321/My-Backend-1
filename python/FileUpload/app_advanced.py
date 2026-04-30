import os
import uuid
import logging
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# ---------------------------------------------------------
# Advanced File Upload Flask Server
# This file complements the principles discussed in `backend_principles_file_upload.md`.
# It demonstrates production-ready file handling, security headers, limits, 
# and logging suitable for cross-device usage.
# ---------------------------------------------------------

# Basic configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
# We restrict extensions sharply to mitigate RCE (Remote Code Execution)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "txt", "pdf", "md", "docx", "zip"}
MAX_FILE_SIZE_MB = 100

app = Flask(__name__)
# The secret key is used to sign session cookies for flash messages.
app.secret_key = "production_ready_secret_key_here!_change_in_prod"

# --- Security & Resource Limits ---
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# MAX_CONTENT_LENGTH enforces a hard limit at the framework level.
# Discarding heavy requests early prevents memory exhaustion (DoS attacks).
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024 

# Setup basic logging to see device connections
logging.basicConfig(level=logging.INFO)

# Ensure the upload folder exists before accepting packets.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------
# Helper Functions Layer
# ---------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """
    Validates the file based on the extension constraint.
    In a real-world scenario, you would also use 'python-magic' 
    to inspect the file's binary header (Magic Numbers).
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename: str) -> str:
    """
    Prevents filename collisions.
    If Device A and Device B both upload 'image.png', they would overwrite each other.
    We prepend a UUID to make the name universally unique.
    """
    safe_name = secure_filename(filename)
    unique_id = str(uuid.uuid4())[:8] # First 8 chars of a UUID
    return f"{unique_id}_{safe_name}"

# ---------------------------------------------------------
# Error Handling Layer
# ---------------------------------------------------------

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    """
    If a user uploads a file larger than MAX_CONTENT_LENGTH,
    the framework throws this error. We must catch it gracefully.
    """
    flash(f"Error: File exceeds the maximum {MAX_FILE_SIZE_MB}MB limit.", "error")
    return redirect(url_for('home'))

# ---------------------------------------------------------
# Routing & Controller Layer
# ---------------------------------------------------------

@app.route("/")
def home():
    """Renders the drag-and-drop secure file hub."""
    return render_template("index_advanced.html")

@app.route("/upload", methods=["POST"])
def upload():
    """
    Handles the multipart/form-data payload.
    It separates the metadata from the file stream.
    """
    # 1. Existence Check: Did the POST request actually include the file part?
    if "file" not in request.files:
        flash("Error: No file part in the request.", "error")
        return redirect(url_for("home"))
    
    file = request.files["file"]
    
    # 2. Empty Check: Did the user submit the form without selecting a file?
    if file.filename == "":
        flash("Error: No file selected.", "error")
        return redirect(url_for("home"))
    
    # 3. Validation Check: Is it an allowed extension?
    if file and allowed_file(file.filename):
        
        # Specialized Business Logic: Convert .txt to .md entirely.
        if file.filename.lower().endswith(".txt"):
            base_name = file.filename.rsplit(".", 1)[0]
            file.filename = f"{base_name}.md"
            logging.info(f"Auto-converted .txt to .md: {file.filename}")

        # 4. Sanitization & Uniqueness Check
        unique_safe_name = generate_unique_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_safe_name)
        
        # 5. Disk Stream Check
        # The file.save() method doesn't load the whole file into RAM. 
        # It reads from the incoming stream and writes directly to the disk in chunks.
        try:
            file.save(save_path)
            logging.info(f"File saved successfully at {save_path}")
            flash(f"Upload successful: {unique_safe_name}", "success")
        except Exception as e:
            logging.error(f"Failed to write file to disk: {e}")
            flash("Error: Could not save the file.", "error")
            
        return redirect(url_for("home"))
    
    else:
        # Invalid extension catch
        flash(f"Error: File type for '{file.filename}' is not allowed.", "error")
        return redirect(url_for("home"))

# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    # Host='0.0.0.0' binds the server to all network interfaces.
    # This allows other devices (a mobile phone, another laptop) on the 
    # same Wi-Fi / Hotspot to access this hub using the host's IP address (e.g., http://192.168.x.x:5000)
    print("🚀 Secure File Hub starting on port 5000...")
    print("📱 To upload from your phone, connect to the same Wi-Fi and visit http://<YOUR_LAPTOP_IP>:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
