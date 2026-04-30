import os
import uuid
import logging
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path

# ---------------------------------------------------------
# Bidirectional File Transfer Flask Server
# UPLOAD: Device -> Laptop
# DOWNLOAD: Laptop -> Device
# This demonstrates production-ready file handling for cross-device scenarios.
# ---------------------------------------------------------

# Basic configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "txt", "pdf", "md", "docx", "zip","html", "pptx","mht","com","exe"}
MAX_FILE_SIZE_MB = 500

app = Flask(__name__)
app.secret_key = "production_ready_secret_key_here!_change_in_prod"

# --- Security & Resource Limits ---
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024 

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------
# Helper Functions Layer
# ---------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """
    Validates the file based on the extension constraint.
    Only allows files with safe extensions to prevent malicious uploads.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename: str) -> str:
    """
    Prevents filename collisions by prepending a unique UUID.
    Without this, simultaneous uploads of 'image.png' from different devices 
    would overwrite each other.
    """
    safe_name = secure_filename(filename)
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}_{safe_name}"

def get_file_list():
    """
    Scans the uploads folder and returns a list of all files.
    Each file includes its name, size (formatted), and modification time.
    """
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            # Only include files, not directories
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                # Convert bytes to human-readable format
                size_mb = round(size / (1024 * 1024), 2)
                files.append({
                    'name': filename,
                    'size': f"{size_mb} MB" if size_mb > 0 else "< 1 MB",
                    'path': file_path
                })
        return sorted(files, key=lambda x: x['name'])
    except Exception as e:
        logging.error(f"Error listing files: {e}")
        return []

def is_safe_path(filepath):
    """
    Security check: Prevents path traversal attacks.
    Example attack: downloading "../../etc/passwd"
    This function ensures the requested file is actually in the uploads folder.
    """
    requested_path = os.path.abspath(filepath)
    uploads_path = os.path.abspath(UPLOAD_FOLDER)
    return requested_path.startswith(uploads_path)

# ---------------------------------------------------------
# Error Handling Layer
# ---------------------------------------------------------

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    """
    Gracefully handle files that exceed the size limit.
    Instead of crashing, we redirect back with a friendly message.
    """
    flash(f"Error: File exceeds the maximum {MAX_FILE_SIZE_MB}MB limit.", "error")
    return redirect(url_for('home'))

@app.errorhandler(404)
def not_found(error):
    """
    Handle requests to endpoints that don't exist.
    """
    flash("Error: The requested resource was not found.", "error")
    return redirect(url_for('home'))

# ---------------------------------------------------------
# Routing & Controller Layer
# ---------------------------------------------------------

@app.route("/")
def home():
    """
    Home route: Renders the dual-tab interface for upload and download.
    """
    return render_template("index_advanced_bidirectional.html")

@app.route("/upload", methods=["POST"])
def upload():
    """
    UPLOAD ENDPOINT
    Handles multipart/form-data POST requests from client devices.
    Flow: Device -> Browser -> HTTP POST -> Server -> Disk
    """
    # 1. Existence Check: Is the 'file' field in the request?
    if "file" not in request.files:
        flash("Error: No file part in the request.", "error")
        return redirect(url_for("home"))
    
    file = request.files["file"]
    
    # 2. Empty Check: Did the user select a file?
    if file.filename == "":
        flash("Error: No file selected.", "error")
        return redirect(url_for("home"))
    
    # 3. Validation Check: Is it an allowed extension?
    if file and allowed_file(file.filename):
        
        # Auto-convert .txt to .md (business logic)
        if file.filename.lower().endswith(".txt"):
            base_name = file.filename.rsplit(".", 1)[0]
            file.filename = f"{base_name}.md"
            logging.info(f"Auto-converted .txt to .md: {file.filename}")

        # 4. Sanitization & Uniqueness
        unique_safe_name = generate_unique_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_safe_name)
        
        # 5. Stream to Disk (doesn't load entire file into RAM)
        try:
            file.save(save_path)
            logging.info(f"File uploaded: {unique_safe_name} from {request.remote_addr}")
            flash(f"Upload successful: {unique_safe_name}", "success")
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            flash("Error: Could not save the file.", "error")
            
        return redirect(url_for("home"))
    
    else:
        flash(f"Error: File type for '{file.filename}' is not allowed.", "error")
        return redirect(url_for("home"))

@app.route("/api/files", methods=["GET"])
def list_files():
    """
    LIST FILES ENDPOINT (JSON API)
    Returns all files in the uploads folder as JSON.
    Called by the Download tab via JavaScript fetch().
    
    Response format:
    {
        "success": true,
        "files": [
            {"name": "doc.pdf", "size": "2.5 MB"},
            {"name": "photo.jpg", "size": "0.85 MB"}
        ]
    }
    """
    files = get_file_list()
    return jsonify({
        "success": True,
        "files": files
    })

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    """
    DOWNLOAD ENDPOINT
    Allows devices to download files from the server.
    Flow: Disk -> Server -> HTTP Response -> Browser Download
    
    Security checks:
    1. Filename validation (no path traversal like "../../../etc/passwd")
    2. File must exist
    3. File must be in the uploads folder
    """
    # 1. Sanitize the filename
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
    
    # 2. Path traversal attack prevention
    if not is_safe_path(file_path):
        logging.warning(f"Blocked suspicious download attempt: {filename}")
        flash("Error: Invalid file path.", "error")
        return redirect(url_for("home"))
    
    # 3. File existence check
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        flash("Error: File not found.", "error")
        logging.warning(f"Download attempted for non-existent file: {filename}")
        return redirect(url_for("home"))
    
    # 4. Stream the file to the client
    try:
        logging.info(f"File downloaded: {filename} by {request.remote_addr}")
        # send_file streams the file from disk directly to the client
        # without loading it entirely into RAM
        return send_file(file_path, as_attachment=True, download_name=safe_filename)
    except Exception as e:
        logging.error(f"Download failed: {e}")
        flash("Error: Could not download the file.", "error")
        return redirect(url_for("home"))

@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    """
    DELETE FILE ENDPOINT
    Allows users to remove files from the server.
    Security: Validates path and checks file exists before deletion.
    """
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
    
    # Security checks
    if not is_safe_path(file_path):
        logging.warning(f"Blocked suspicious delete attempt: {filename}")
        return jsonify({"success": False, "error": "Invalid file path"}), 403
    
    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "File not found"}), 404
    
    try:
        os.remove(file_path)
        logging.info(f"File deleted: {filename} by {request.remote_addr}")
        return jsonify({"success": True, "message": f"Deleted {filename}"})
    except Exception as e:
        logging.error(f"Delete failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Bidirectional File Hub starting on port 5000...")
    print("📤 UPLOAD: Send files from your device to the laptop")
    print("📥 DOWNLOAD: Get files from the laptop to your device")
    print("🌐 Connect to http://<YOUR_LAPTOP_IP>:5000 from any device on the same Wi-Fi")
    app.run(host="0.0.0.0", port=5000, debug=True)
