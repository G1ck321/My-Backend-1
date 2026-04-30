from flask import Flask, jsonify, request, render_template
from flask import redirect, url_for, flash
# secure_filename => prevents malicious filenames (like "../../../../etc/passwd")
# which could allow a hacker to save files to arbitrary system folders.
from werkzeug.utils import secure_filename
# filepath handling and creation (interacting with the Operating System)
import os

# --- 1. CONFIGURATION ---
# Define where uploaded files will be stored relative to this script.
UPLOAD_FOLDER = "uploads"
# Define a strict set of allowed extensions. Extensons not in this list will be rejected.
# This prevents users from uploading executable code (.exe, .php, .sh) which could harm the server.
ALLOWED = {"png","jpg","jpeg","gif","txt","pdf","md","docx","zip","exe"}

# Initialize the Flask application instance
app = Flask(__name__)

# Assign the specific configurations to the Flask app config dictionary
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Prevent DoS (Denial of Service) attacks by capping the maximum upload size.
# Here, it is capped at approx 811 MB (811 * 1024 KB * 1024 Bytes).
app.config["MAX_CONTENT_LENGTH"] = 811 * 1024 * 1024 
# Secret key is required to sign session cookies, which 'flash' uses to pass messages between requests securely.
app.secret_key = "mysert!5477"

# Safely create the uploads directory if it doesn't already exist. (exist_ok=True prevents crashes if it's there)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
print(os.listdir(UPLOAD_FOLDER), os.listdir(UPLOAD_FOLDER)[2].rsplit(".",1)[1] in ALLOWED)

# --- 2. VALIDATION HELPERS ---
def allowed_file(filename: str):
    """
    Checks if a given filename has a valid extension.
    1. '.' in filename: ensures the file actually has an extension.
    2. rsplit(".", 1)[1]: splits from the right exactly once to get the extension.
    3. .lower(): normalizes it so 'IMG.PNG' and 'img.png' are treated identically.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

# --- 3. ROUTES / CONTROLLERS ---

@app.route("/")
def home():
    """
    Serves the upload form HTML page.
    The client (browser) uses this to understand what inputs to show the user.
    """
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """
    The main controller that processes the incoming 'multipart/form-data' request.
    It ensures the file exists, validates it, and saves it to the local disk.
    """
    
    # 1. Existence Check: Did the HTTP POST request actually contain a part named 'file'?
    if "file" not in request.files:
        flash("no file part")
        return redirect(url_for("home"))
    
    file = request.files["file"]
    
    # Helper scope function: Renames a file if it already exists to prevent overwriting.
    def fileExists(fileName):
        if fileName in os.listdir(UPLOAD_FOLDER):
            # Example: note.md becomes note(1).md
            fileNamed = fileName.split(".",1)[0] + "(1)" + ".md"
            safe_name = secure_filename(fileNamed)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(save_path)
            flash(f"Upload successful:{safe_name}")
            print(f"Upload successful:{safe_name}")
            return redirect(url_for("home"))
        
    # 2. Empty Selection Check: Did the user click 'submit' without actually choosing a file?
    if file.filename == "":
        flash("Error: No file selected")
        return redirect(url_for("home"))
    
    # 3. Extension Validation Check: Is it an allowed file type?
    if file and allowed_file(file.filename):
        
        # Specialized Logic: If the file is a text file (.txt), convert the extension to Markdown (.md).
        print((file.filename.rsplit(".",1)[0]),"dhdh")
        if file.filename[:-4:-1] == "txt":
            # Repackage text file as md.
            file.filename = file.filename.rsplit(".",1)[0] + ".md"
            safe_name = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(save_path)
            fileExists(file.filename)
            flash(f"Upload successful:{safe_name}")
            print(f"Upload successful:{safe_name}")
            return redirect(url_for("home"))
            
        # 4. Save Logic: If it's a valid, non-txt file (like an image).
        safe_name = secure_filename(file.filename)
        # os.path.join properly formats the path depending on OS (Windows '\\', Linux/Mac '/')
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
        
        # Streams the file directly to your disk rather than loading it entirely into RAM memory.
        file.save(save_path)
        
        print(31)
        return redirect(url_for("home"))
    
    else:
        # Invalid extension handling.
        flash("Error: File type not allowed.")
        print("File type is not allowed")
        return redirect(url_for("home"))

if __name__ == "__main__":
    # host="0.0.0.0" lets Flask listen on all network interfaces.
    # This allows other devices on the same Wi-Fi/hotspot to connect to this server
    # by visiting the laptop's local IP address (e.g., http://192.168.1.10:5000).
    app.run(host="0.0.0.0", port=5000, debug=True)