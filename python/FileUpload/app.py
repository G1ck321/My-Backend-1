from flask import Flask, jsonify, request,render_template
from flask import redirect, url_for, flash
#secure_filename =>prevents malicious filenames
from werkzeug.utils import secure_filename
#filepath hanling and creation
import os

UPLOAD_FOLDER= "uploads"
ALLOWED = {"png","jpg","jpeg","gif","txt","pdf","md"}

app = Flask(__name__)

app.config["UPLOAD_FOLDER"]= UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16*1024*1024 #16MB max limit
app.secret_key = "mysert!5477"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#file validation
def allowed_file(filename:str):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED
#rsplit splits from the right once

#show upload page
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """ensures file exists, 
    validate filename, 
    savefile to upload folder
    """
    #Checks if file exists
    if "file" not in request.files:
        flash("no file part")
        return redirect(url_for("home"))
    
    file = request.files["file"]
    
    #No selected file
    if file.filename =="":
        flash("Error: No file selected")
        return redirect(url_for("home"))
    
    #Validate file extension
    if file and allowed_file(file.filename):
        #convert txt to md
        print((file.filename.rsplit(".",1)[0]),"dhdh")
        if file.filename[:-4:-1]=="txt":
            file.filename = file.filename.rsplit(".",1)[0]+".md"
            safe_name =secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(save_path)
            flash(f"Upload successful:{safe_name}")
            return(redirect(url_for("home")))
        
        safe_name = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
        file.save(save_path)
        flash(f"Upload successful:{safe_name}")
        return redirect(url_for("home"))
    
    else:
        flash("Error: File type not allowed.")
        print("File type is not allowed")
        return redirect(url_for("home"))

if __name__ == "__main__":
    #host 0.0.0 let's flask listen on all network interfaces
    # so other devices on same hotspot can connect
    app.run(host="0.0.0.0", port=5000, debug=True)