# Backend File Upload & Transfer: Complete Masterclass
## From First Principles to Production-Ready Systems

---

## Table of Contents
1. [The Post Office Analogy (Deep Dive)](#the-post-office-analogy-deep-dive)
2. [Fundamental Concepts](#fundamental-concepts)
3. [Architecture Layers](#architecture-layers)
4. [Building Blocks with Code Examples](#building-blocks-with-code-examples)
5. [Security & Validation](#security--validation)
6. [Bidirectional Transfer Explained](#bidirectional-transfer-explained)
7. [Advanced Concepts](#advanced-concepts)
8. [Standout Project Ideas](#standout-project-ideas)
9. [Key Resources](#key-resources)

---

## The Post Office Analogy (Deep Dive)

Imagine you're running an International Post Office that handles packages in **both directions**.

### The Complete Flow

**SCENARIO 1: Device (Client) → Laptop (Server) [UPLOAD]**
```
Your Phone (192.168.1.5)
    ↓
[Browser makes HTTP POST request with multipart/form-data]
    ↓
Travels across Wi-Fi network
    ↓
Arrives at Laptop Server (listening on 0.0.0.0:5000)
    ↓
[Server receives request, validates, sanitizes]
    ↓
Writes file stream to disk (uploads/ folder)
    ↓
Sends success response back to phone
    ↓
Your Phone receives confirmation
```

**SCENARIO 2: Laptop (Server) → Device (Client) [DOWNLOAD]**
```
Your Phone requests file list
    ↓
Laptop server scans /uploads folder
    ↓
Returns JSON list (doesn't send actual files yet, just metadata)
    ↓
You click "Download image.jpg"
    ↓
Phone sends GET request for /download/image.jpg
    ↓
Server verifies file exists & is safe (path traversal check)
    ↓
Server streams file bytes to phone as HTTP response
    ↓
Browser receives binary data, saves as download
```

### Why This Matters

Without a server in the middle, your phone cannot directly read your laptop's disk. The HTTP protocol provides the **bridge**. Your server acts as the **clerk** who:
- Checks if your package is safe (malware scan)
- Renames it if a duplicate arrives (UUID collision prevention)
- Stores it in the correct shelf (file path management)
- Retrieves it when you ask (download/streaming)

---

## Fundamental Concepts

### 1. **Statelessness: The Golden Rule**

**Concept**: Each HTTP request is **independent**. The server doesn't remember who you are between requests.

**Why This Matters**:
```
Request 1: POST /upload with file.jpg
- Server processes it
- Saves it to disk
- Responds with 200 OK

Request 2: GET /list
- Server has NO MEMORY of Request 1
- It must read from disk to list files
- It cannot assume file.jpg is still there

BAD ASSUMPTION:
  server_memory = {"uploaded_file": "file.jpg"}
  # This only exists in RAM, dies when server restarts!

CORRECT APPROACH:
  # Read from persistent storage (disk/database)
  files = os.listdir("uploads/")
  # This survives server restarts
```

**Real-World Impact**: If your Flask server crashes and restarts, a file uploaded 5 minutes ago is still there because it was written to disk, not RAM.

### 2. **Streams vs. Loading Entire Files Into RAM**

**Concept**: Large files should be processed in **chunks**, not loaded entirely into memory.

**Example Problem**:
```python
# BAD: If user uploads 500MB file, this loads ALL 500MB into RAM
file_content = request.files['file'].read()
# Now your server is using 500MB+ just for this one request
# If 10 users do this simultaneously, you need 5GB RAM!
# This is a Denial of Service (DoS) vulnerability
```

**Correct Approach**:
```python
# GOOD: Flask's file.save() handles streaming automatically
file.save(filepath)
# Internally does:
#   while True:
#       chunk = request.stream.read(16384)  # 16KB at a time
#       if not chunk: break
#       disk_file.write(chunk)
# Peak RAM usage = 16KB, no matter file size!
```

**Code Visualization**:
```
Without Streaming (BAD):
  Time →
  RAM: [0%] → [50%] → [100%] → [100%] (holds 500MB) → [0%] after save
  
With Streaming (GOOD):
  Time →
  RAM: [0%] → [0.5%] → [0.5%] → [0.5%] (always ~16KB) → [0%]
```

### 3. **Never Trust the Client**

**Concept**: Browser validation is for **User Experience**, not **Security**. Server validation is mandatory.

**HTML Level** (User Experience):
```html
<input type="file" accept=".jpg,.png" />
<!-- This helps users, but is TRIVIAL to bypass -->
```

**Hacker's Perspective**:
```javascript
// In browser console, attacker uploads a .exe renamed to .jpg:
const formData = new FormData();
const malware = new File([...], "innocent.jpg", {type: "image/jpeg"});
formData.append('file', malware);
fetch('/upload', {method: 'POST', body: formData});
// The .jpg extension is FAKE. Inside, it's actually a virus!
```

**Server-Side Validation** (Security):
```python
# CORRECT: Check the ACTUAL file content, not the extension
def validate_file(file):
    # 1. Check extension (first line of defense)
    if not file.filename.endswith('.jpg'):
        return False  # Reject immediately
    
    # 2. Read first few bytes (Magic Numbers)
    file_header = file.read(4)
    file.seek(0)  # Reset position for actual save
    
    # JPEG files always start with: FF D8 FF
    if file_header[:3] != b'\xff\xd8\xff':
        return False  # It's not actually a JPEG!
    
    return True
```

### 4. **Path Traversal: The "../" Attack**

**Concept**: Hackers can use `../` to escape the intended folder.

**Example Attack**:
```
Attacker requests: GET /download/../../../../etc/passwd
Naive server does: os.path.join("uploads/", "../../../../etc/passwd")
Result: Server accidentally serves /etc/passwd (system file!)

Correct server does:
  requested = "../../../../etc/passwd"
  requested_path = os.path.abspath(os.path.join("uploads/", requested))
  # = /home/user/etc/passwd (wrong path, doesn't exist)
  
  uploads_path = os.path.abspath("uploads/")
  # = /home/user/uploads
  
  if not requested_path.startswith(uploads_path):
      return 403  # REJECTED!
```

---

## Architecture Layers

Professional backends separate concerns into layers:

```
┌─────────────────────────────────────┐
│      PRESENTATION (Flask Routes)    │  @app.route("/upload")
│                                     │  Returns HTML/JSON responses
├─────────────────────────────────────┤
│      BUSINESS LOGIC (Validation)    │  allowed_file(), generate_unique_filename()
│                                     │  File processing, transformations
├─────────────────────────────────────┤
│      DATA ACCESS LAYER              │  File I/O, reading from disk
│                                     │  Database queries (if applicable)
├─────────────────────────────────────┤
│      STORAGE (Disk/Cloud)           │  uploads/ folder, S3, etc.
└─────────────────────────────────────┘
```

**Why Layers Matter**:
- **Testability**: You can test validation without touching the disk
- **Reusability**: Other parts of your app can use the same validation
- **Maintenance**: Change one layer without affecting others
- **Scalability**: Swap local disk storage for S3 with minimal code changes

---

## Building Blocks with Code Examples

### Block 1: File Validation

```python
# ============ VALIDATION LAYER ============

ALLOWED_EXTENSIONS = {"jpg", "png", "pdf", "txt", "md"}
MAX_FILE_SIZE_MB = 100

def is_valid_extension(filename: str) -> bool:
    """
    Check if file has an allowed extension.
    
    Why important:
    - Prevents uploads of .exe, .php, .sh (executable files)
    - Executables on the server can be compromised if not secure
    
    Example:
      is_valid_extension("photo.jpg")   → True
      is_valid_extension("photo.jpg.exe") → False (.exe is the real extension!)
      is_valid_extension("photo")        → False (no extension)
    """
    if '.' not in filename:
        return False
    
    # rsplit() splits from the RIGHT, once
    # "document.backup.pdf" → ["document.backup", "pdf"]
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS

def is_valid_size(file) -> bool:
    """
    Check if file size is within limit.
    
    This prevents:
    - Filling up disk (DoS attack)
    - Server crashing due to low disk space
    
    Note: Flask's MAX_CONTENT_LENGTH also enforces this,
    but we double-check for better error messages.
    """
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to start
    
    size_mb = file_size / (1024 * 1024)
    return size_mb <= MAX_FILE_SIZE_MB

def is_safe_filename(filename: str) -> bool:
    """
    Check if filename contains dangerous characters.
    
    Dangerous patterns:
    - "../" (path traversal)
    - "/etc/passwd" (absolute path)
    - Characters that break filesystems
    
    secure_filename() from werkzeug handles this:
    """
    from werkzeug.utils import secure_filename
    safe = secure_filename(filename)
    return safe == filename or safe  # Must result in something non-empty
```

### Block 2: Filename Sanitization

```python
# ============ SANITIZATION LAYER ============

import os
import uuid
from werkzeug.utils import secure_filename

def generate_safe_filename(original_filename: str) -> str:
    """
    Transform a user-provided filename into something safe for storage.
    
    Problems we solve:
    1. Filename Collisions
       - User A uploads "photo.jpg"
       - User B uploads "photo.jpg"
       - Second user's file overwrites first user's file!
       
    2. Invalid Characters
       - Filename: "my file <3.jpg"
       - Some filesystems don't support <, >, |, etc.
       
    3. Path Traversal
       - Filename: "../../secret.txt"
       - We must prevent escaping the uploads/ folder
    
    Solution: Use UUID (Universally Unique Identifier)
      Every file gets a unique 36-character ID
      Probability of collision: 1 in 5.3 × 10^36
    
    Example transformation:
      Input:  "my photo (2).jpg"
      Safe:   "my_photo_2_.jpg" (secure_filename)
      UUID:   "f7e8c9a1-..." (first 8 chars: f7e8c9a1)
      Final:  "f7e8c9a1_my_photo_2_.jpg"
    """
    # Step 1: Use werkzeug to remove dangerous characters
    safe_name = secure_filename(original_filename)
    
    # Step 2: Generate unique identifier (first 8 chars of UUID)
    unique_id = str(uuid.uuid4())[:8]
    # uuid.uuid4() example output: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    # First 8 chars: "a1b2c3d4"
    
    # Step 3: Combine them
    return f"{unique_id}_{safe_name}"

# Real-world example:
filename = generate_safe_filename("MyPhoto (1).jpg")
print(filename)
# Output: "a1b2c3d4_myphoto_1_.jpg"
# Two users can both upload "MyPhoto (1).jpg" and they won't collide!
```

### Block 3: File Storage Management

```python
# ============ STORAGE LAYER ============

import os
from pathlib import Path

class FileStorage:
    """
    Manages file storage operations.
    Separates storage logic from routes.
    
    Why a class?
    - Can easily swap implementations later
    - Example: FileStorage to S3Storage (just change backend)
    """
    
    def __init__(self, upload_folder: str):
        """Initialize storage with a folder path."""
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_file(self, file, unique_filename: str) -> dict:
        """
        Save a file to disk.
        
        Returns metadata about the saved file.
        """
        save_path = os.path.join(self.upload_folder, unique_filename)
        
        try:
            file.save(save_path)  # Streaming save (memory efficient)
            
            # Get file info for response
            file_size = os.path.getsize(save_path)
            
            return {
                "success": True,
                "filename": unique_filename,
                "original_name": file.filename,
                "size_bytes": file_size,
                "path": save_path
            }
        except IOError as e:
            return {
                "success": False,
                "error": f"Disk write failed: {str(e)}"
            }
    
    def list_files(self) -> list:
        """
        Get all files in storage.
        
        Returns list of file info dicts.
        """
        files = []
        try:
            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)
                
                # Only include files, not directories
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    size_mb = round(size / (1024 * 1024), 2)
                    
                    files.append({
                        "name": filename,
                        "size": size_mb,
                        "size_formatted": f"{size_mb} MB"
                    })
        except OSError as e:
            print(f"Error listing files: {e}")
        
        return sorted(files, key=lambda x: x['name'])
    
    def is_safe_path(self, filepath: str) -> bool:
        """
        Prevent path traversal attacks.
        
        Ensures the requested file is actually in uploads/ folder.
        """
        requested = os.path.abspath(filepath)
        allowed = os.path.abspath(self.upload_folder)
        return requested.startswith(allowed)
    
    def delete_file(self, filename: str) -> bool:
        """Safely delete a file."""
        filepath = os.path.join(self.upload_folder, filename)
        
        if not self.is_safe_path(filepath):
            return False  # Reject suspicious path
        
        if not os.path.exists(filepath):
            return False  # File doesn't exist
        
        try:
            os.remove(filepath)
            return True
        except OSError:
            return False

# Usage example:
storage = FileStorage("uploads/")
result = storage.save_file(file_object, "abc123_document.pdf")
if result["success"]:
    print(f"File saved: {result['filename']}")
```

### Block 4: HTTP Request/Response Cycle

```python
# ============ ROUTING / CONTROLLER LAYER ============

from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
storage = FileStorage("uploads/")

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Complete HTTP upload flow.
    
    Network Flow:
    ┌─────────────────────────────────────────┐
    │ Browser sends HTTP POST with file       │
    │ Content-Type: multipart/form-data       │
    │ Body: [boundary markers] [file data]    │
    └─────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────┐
    │ Server receives request.files['file']   │
    │ This is a FileStorage object with:      │
    │  - .filename (string)                   │
    │  - .stream (file-like object)           │
    │  - .save() (method to write to disk)    │
    └─────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────┐
    │ Server validates & processes            │
    │ Returns JSON response                   │
    └─────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────┐
    │ Browser receives response, updates UI   │
    └─────────────────────────────────────────┘
    """
    
    # 1. CHECK: Did the form include a 'file' field?
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file in request"}), 400
    
    file = request.files["file"]
    
    # 2. CHECK: Did user select a file (not just click submit)?
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    # 3. VALIDATE: Is it an allowed file type?
    if not is_valid_extension(file.filename):
        return jsonify({
            "success": False,
            "error": f"File type '{file.filename.split('.')[-1]}' not allowed"
        }), 400
    
    # 4. VALIDATE: Is file size acceptable?
    if not is_valid_size(file):
        return jsonify({
            "success": False,
            "error": f"File exceeds {MAX_FILE_SIZE_MB}MB limit"
        }), 413  # 413 = Payload Too Large
    
    # 5. SANITIZE: Create safe filename
    safe_name = generate_safe_filename(file.filename)
    
    # 6. SAVE: Write to disk
    result = storage.save_file(file, safe_name)
    
    if result["success"]:
        return jsonify({
            "success": True,
            "message": f"File saved as {result['filename']}",
            "data": result
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result["error"]
        }), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """
    Complete HTTP download flow.
    
    Network Flow:
    ┌─────────────────────────────────────────┐
    │ Browser requests: GET /download/file.pdf│
    └─────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────┐
    │ Server:                                 │
    │ 1. Validate filename (no ../attacks)    │
    │ 2. Check file exists                    │
    │ 3. Send file as response body           │
    └─────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────┐
    │ Browser receives binary data            │
    │ OS saves to Downloads/ folder           │
    └─────────────────────────────────────────┘
    """
    
    # 1. SANITIZE: Prevent path traversal
    safe_filename = secure_filename(filename)
    filepath = os.path.join(storage.upload_folder, safe_filename)
    
    # 2. SECURITY: Verify file is actually in uploads/
    if not storage.is_safe_path(filepath):
        return jsonify({"error": "Invalid file path"}), 403
    
    # 3. CHECK: File exists?
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    # 4. SEND: Stream file to client
    try:
        return send_file(
            filepath,
            as_attachment=True,  # Tell browser to download, not display
            download_name=safe_filename  # What to name the file
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## Security & Validation

### Defense Layers (Layered Security)

```python
# Layer 1: Framework Level (Flask)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
# If request > 100MB, Flask rejects it before app code runs

# Layer 2: Route Level (Function)
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return error  # Reject immediately

# Layer 3: Validation Level
    if not is_valid_extension(file.filename):
        return error

# Layer 4: Sanitization Level
    safe_name = generate_safe_filename(file.filename)

# Layer 5: Storage Level
    if not storage.is_safe_path(filepath):
        return error
```

### Common Attacks & Defenses

```python
# ============ ATTACK #1: Filename Collision ============
# Attack: Two users upload "photo.jpg", second overwrites first
# Defense: Use UUID
def generate_safe_filename(filename):
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}_{secure_filename(filename)}"

# ============ ATTACK #2: Path Traversal ============
# Attack: User requests "../../../../etc/passwd"
# Defense: Validate requested path is within uploads/
def is_safe_path(filepath):
    requested = os.path.abspath(filepath)
    allowed = os.path.abspath("uploads/")
    return requested.startswith(allowed)

# ============ ATTACK #3: Malicious File Extension ============
# Attack: Upload "virus.exe" renamed to "virus.jpg"
# Defense: Check actual file content (magic numbers)
def validate_image_file(filepath):
    with open(filepath, 'rb') as f:
        header = f.read(4)
        # JPEG files start with: FF D8 FF E0
        if header[:3] != b'\xff\xd8\xff':
            os.remove(filepath)
            return False
    return True

# ============ ATTACK #4: Resource Exhaustion (DoS) ============
# Attack: Upload infinite files to fill disk
# Defense: Quota per user, rate limiting
MAX_FILES_PER_USER = 10
MAX_STORAGE_GB = 100

def check_user_quota(user_id):
    user_files = count_user_files(user_id)
    user_storage = get_user_storage_used(user_id)
    
    if user_files >= MAX_FILES_PER_USER:
        return False, "File limit reached"
    if user_storage >= MAX_STORAGE_GB:
        return False, "Storage quota exceeded"
    return True, "OK"
```

---

## Bidirectional Transfer Explained

### How Downloads Work

```
┌──────────────────────────────────────────────────────┐
│ User clicks "Download button" for "photo.jpg"        │
└──────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────┐
│ Browser generates:                                   │
│ GET /download/abc123_photo.jpg HTTP/1.1             │
│ Host: 192.168.1.10:5000                            │
└──────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────┐
│ Server receives request                              │
│ 1. Extract filename: "abc123_photo.jpg"             │
│ 2. Construct path: "uploads/abc123_photo.jpg"       │
│ 3. Verify path doesn't escape (is_safe_path)        │
│ 4. Check file exists                                │
│ 5. Open file for reading                            │
└──────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────┐
│ Server sends HTTP response:                          │
│ HTTP/1.1 200 OK                                     │
│ Content-Type: image/jpeg                            │
│ Content-Length: 2048576 (2MB in bytes)             │
│ Content-Disposition: attachment; filename=abc123... │
│                                                      │
│ [Binary file data: 2MB of JPEG bytes]              │
└──────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────┐
│ Browser receives response                            │
│ 1. Sees Content-Disposition: attachment             │
│    → Triggers "Save File" dialog                    │
│ 2. User selects location (e.g., Downloads/)        │
│ 3. Browser writes binary data to disk               │
└──────────────────────────────────────────────────────┘
```

### Streaming Downloads (Memory Efficiency)

```python
# BAD: Load entire file into memory first
@app.route("/download/<filename>")
def download_bad(filename):
    with open(f"uploads/{filename}", 'rb') as f:
        file_data = f.read()  # ← If file is 1GB, uses 1GB RAM!
    return file_data

# GOOD: Stream file to client in chunks
@app.route("/download/<filename>")
def download_good(filename):
    return send_file(filepath, as_attachment=True)
    # Internally:
    #   with open(filepath, 'rb') as f:
    #       while True:
    #           chunk = f.read(8192)  # 8KB at a time
    #           if not chunk: break
    #           send_to_client(chunk)
    # Peak RAM usage = 8KB, no matter file size!
```

### Getting File List

```python
# Frontend requests list of available files
# GET /api/files

# Backend returns JSON
{
    "success": true,
    "files": [
        {
            "name": "abc123_document.pdf",
            "size": "2.5 MB"
        },
        {
            "name": "def456_photo.jpg",
            "size": "0.85 MB"
        }
    ]
}

# Frontend displays list, user can click to download
```

---

## Advanced Concepts

### 1. Chunked Uploads (Resume Capability)

**Problem**: Upload fails at 95% of a 1GB file. Must start over?

**Solution**: Upload in 5MB chunks. Only re-upload failed chunk.

```python
# Example: Tus.io Protocol Implementation
# https://tus.io/protocols/resumable-upload.html

# Step 1: Client initiates upload
POST /files
Content-Length: 0
Upload-Length: 1000000000  # 1GB
Response: Location: /files/abc123xyz

# Step 2: Client uploads chunk 1 (0-5MB)
PATCH /files/abc123xyz
Content-Range: bytes 0-5242879/1000000000
[5MB of file data]

# Step 3: Connection drops at 50%...
# Step 4: Client resumes
PATCH /files/abc123xyz
Upload-Offset: 524288000  # Resume from byte 500MB
Content-Range: bytes 524288000-529531999/1000000000
[Next 5MB of data]
```

### 2. Content Delivery Networks (CDNs)

**Problem**: User in Australia downloads file from server in USA. Slow!

**Solution**: Use CDN to cache files globally.

```
Without CDN:
  Australia User → 300ms latency → USA Server
  Slow download (2 Mbps internet)

With CDN:
  Australia User → 10ms latency → CDN Edge in Sydney
  Fast download (100 Mbps cache)
  
CDN syncs with origin server every hour
```

### 3. Virus Scanning Integration

```python
import subprocess

def scan_uploaded_file(filepath):
    """
    Use ClamAV (open-source antivirus) to scan files.
    
    Production-grade backends should do this.
    """
    try:
        result = subprocess.run(
            ['clamscan', filepath],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode != 0:  # Virus detected
            os.remove(filepath)
            return {"safe": False, "reason": "Virus detected"}
        
        return {"safe": True}
    except Exception as e:
        # If scanning fails, be cautious
        return {"safe": False, "reason": "Scan failed"}
```

### 4. Database Integration

Instead of just storing files, track metadata in a database:

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255))
    stored_filename = db.Column(db.String(255), unique=True)
    file_size = db.Column(db.Integer)  # in bytes
    mime_type = db.Column(db.String(50))
    uploaded_by = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    virus_scanned = db.Column(db.Boolean, default=False)
    is_safe = db.Column(db.Boolean, nullable=True)
    download_count = db.Column(db.Integer, default=0)

# Now you can:
# - Track who uploaded what
# - See when files were uploaded
# - Count downloads
# - Audit all activities
```

---

## Standout Project Ideas

### Project 1: Local-First, End-to-End Encrypted Drop
**Why it stands out**: Security focus, WebCrypto API, no server-side decryption

```
User flow:
1. User selects file on phone
2. File encrypted in browser using AES-256-GCM
3. Encrypted blob sent to server (server sees gibberish)
4. User gets magic link: example.com/?key=xyz
5. Share link with friend
6. Friend decrypts locally in their browser
7. Server never knows what the file is!
```

**Tech Stack**: 
- Frontend: React + TweetNaCl.js (encryption)
- Backend: Flask + minimal (just storage)

**Portfolio Impact**: Shows deep understanding of security, cryptography, modern web APIs.

### Project 2: P2P File Transfer via WebRTC
**Why it stands out**: Direct device-to-device, no central storage

```
User flow:
1. Laptop opens app → gets unique ID "abc123"
2. Phone opens app, enters "abc123"
3. Backend acts as signaling server only
4. Devices establish WebRTC data channel
5. File transfers directly (not through server)
6. Server bandwidth = 0
```

**Tech Stack**:
- Frontend: Vue.js + simple-peer (WebRTC wrapper)
- Backend: Flask + Socket.IO (signaling only)

**Portfolio Impact**: Shows understanding of WebRTC, real-time communication, optimization.

### Project 3: Real-Time Video Transcoder with Progress Streaming
**Why it stands out**: Asynchronous processing, WebSockets, complex backend

```
User flow:
1. Upload 2GB video file
2. Server queues job to FFmpeg worker
3. WebSocket streams: "5% complete", "10%", "15%"...
4. User sees live progress bar
5. When done: "Ready to download"
```

**Tech Stack**:
- Frontend: React + WebSockets
- Backend: Flask + Celery (async tasks) + Redis (job queue) + FFmpeg
- Architecture: Microservices (upload service, transcoding worker)

**Portfolio Impact**: Shows full-stack knowledge, asynchronous processing, scalability.

---

## Key Resources

### Official Documentation
- **Flask Upload Documentation**: https://flask.palletsprojects.com/en/latest/patterns/fileuploads/
- **werkzeug.utils**: https://werkzeug.palletsprojects.com/en/latest/utils/#module-werkzeug.utils
- **OWASP File Upload Cheatsheet**: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

### Must-Read Concepts
- **12-Factor App**: https://12factor.net/ (serverless, statelessness, config management)
- **REST API Best Practices**: https://restfulapi.net/
- **Streaming in HTTP**: https://en.wikipedia.org/wiki/Chunked_transfer_encoding

### Libraries & Tools
- **Tus.io** (Resumable uploads): https://github.com/tus/tus-py-server
- **python-magic** (File type detection): https://github.com/ahupp/python-magic
- **ClamAV** (Antivirus): https://www.clamav.net/
- **Celery** (Task queue): https://docs.celeryproject.io/
- **simple-peer** (WebRTC): https://github.com/feross/simple-peer

### Learning Paths
1. **Beginner**: Build this file upload app, add database
2. **Intermediate**: Add user authentication, quota management, virus scanning
3. **Advanced**: Implement resumable uploads, video transcoding, CDN integration
4. **Expert**: Distributed storage (S3), horizontal scaling, multi-region sync

---

## Summary: The Three Core Truths

1. **Always use streams, never load entire files into RAM**
   - Peak memory usage should be constant, independent of file size

2. **Server-side validation is mandatory, client-side is UX only**
   - Never trust the file extension or browser validations

3. **Separation of concerns saves your sanity**
   - Routes → Validation → Storage: Keep them separate and testable

These principles transcend language, framework, and hosting platform. A Node.js backend follows the same rules as a Python one, and a cloud-native system uses the same concepts as a bare-metal server.
