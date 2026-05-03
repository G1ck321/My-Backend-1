
"""
========================================================================
app.py - Flask Application with Flash System & Logging
========================================================================

COMPREHENSIVE EXPLANATION OF FLASH & LOGGING SYSTEMS

This file demonstrates:
1. Flask's Flash system (user feedback across requests)
2. Python's Logging system (developer debugging)
3. How they work together in a real application
4. Common patterns and best practices
========================================================================
"""

from flask import Flask, flash, redirect, render_template, request, url_for, session
import logging
from logger_setup import setup_logger
from datetime import datetime

# ============================================================================
# 1. APPLICATION INITIALIZATION
# ============================================================================

app = Flask(__name__)

# CRITICALLY IMPORTANT: Secret key must be set for sessions to work
# Flash uses sessions behind the scenes, and sessions are encrypted
# If you restart Flask, users' flash messages disappear (expected behavior)
# In production, use environment variables: os.environ.get('SECRET_KEY')
app.secret_key = 'your_super_secret_key_change_me_in_production'

# Initialize logging
logger = setup_logger(app, log_level=logging.DEBUG)

logger.info("Flask application initialized")
logger.info(f"Secret key set: {'*' * 20}")  # Don't log actual key in production!


# ============================================================================
# 2. UNDERSTANDING FLASK'S FLASH SYSTEM
# ============================================================================

"""
THE FLASH SYSTEM ANALOGY: A Bulletin Board Outside Your Classroom
==================================================================

SCENARIO: You want to tell students something important, but you'll only 
see them after lunch. What do you do?

Option A (BAD): Stand by the door and shout at each student.
- Some hear you
- Some don't
- You have to repeat constantly
→ This is like storing messages in a global variable

Option B (GOOD): Write on the bulletin board:
- Students see the message when they leave
- They read it once, then it's gone
- Next day, you write a new message
→ This is exactly how Flask's flash() works!

HOW FLASH WORKS IN FLASK:
1. User submits form (POST request)
2. Server calls flash("Success!") → Message stored in SESSION
3. Server redirects user (typically to GET request)
4. New page loads, calls get_flashed_messages() → Displays messages
5. Messages AUTOMATICALLY DELETED after being retrieved
6. If user refreshes, messages are gone

WHY REDIRECT AFTER FLASH?
If you return render_template directly (without redirect):
    @app.route('/form', methods=['POST'])
    def submit_form():
        flash("Success!")
        return render_template('result.html')  # BAD: No redirect

Problem: If user refreshes the page, the POST request is resent!
Browser asks: "Send POST data again?" → Creates duplicate!

Solution: Always redirect after form submission:
    @app.route('/form', methods=['POST'])
    def submit_form():
        flash("Success!")
        return redirect(url_for('show_result'))  # Good: Redirect to GET

This is the Post-Redirect-Get (PRG) pattern - a web best practice.
"""


# ============================================================================
# 3. BASIC FLASH EXAMPLE
# ============================================================================

@app.route('/')
def index():
    """
    Home page - displays the form where users enter data.
    
    Flash messages from previous requests appear here automatically.
    The get_flashed_messages() is called in the template:
    
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    """
    logger.debug("User visiting home page")
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit_form():
    """
    Handles form submission.
    
    FLOW:
    1. Receive data from form (POST request)
    2. Validate input
    3. Flash appropriate message
    4. Redirect back to home page (GET request)
    5. Home page displays flash message
    
    This demonstrates the POST-REDIRECT-GET pattern.
    """
    # Extract form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    
    logger.debug(f"Form submission received: name={name}, email={email}")
    
    # ========================================================================
    # VALIDATION LAYER
    # ========================================================================
    
    # Empty check
    if not name:
        logger.warning("Form submission failed: name is empty")
        flash("❌ Error: Name cannot be empty", category='error')
        return redirect(url_for('index'))
    
    # Length check
    if len(name) < 2:
        logger.warning(f"Form submission failed: name too short ({len(name)} chars)")
        flash("❌ Error: Name must be at least 2 characters", category='error')
        return redirect(url_for('index'))
    
    # Email validation (basic)
    if email and '@' not in email:
        logger.warning(f"Form submission failed: invalid email format ({email})")
        flash("❌ Error: Invalid email format", category='error')
        return redirect(url_for('index'))
    
    # ========================================================================
    # SUCCESS: All validation passed
    # ========================================================================
    
    logger.info(f"Form successfully submitted by user: {name} ({email})")
    
    # Flash supports categories: 'success', 'error', 'warning', 'info'
    # Use categories to style different message types differently in template
    flash(f"✅ Welcome, {name}! Your data has been saved.", category='success')
    
    if email:
        flash(f"📧 Confirmation email will be sent to {email}", category='info')
    
    return redirect(url_for('index'))


# ============================================================================
# 4. ADVANCED FLASH PATTERNS
# ============================================================================

@app.route('/user/<username>')
def user_profile(username):
    """
    Display user profile with optional messages.
    
    This demonstrates conditional flashing:
    - Flash only appears under certain conditions
    - Useful for showing results of background operations
    """
    logger.debug(f"Loading profile for user: {username}")
    
    # Simulate checking if user exists
    valid_users = ['alice', 'bob', 'charlie']
    
    if username not in valid_users:
        logger.warning(f"User profile requested for non-existent user: {username}")
        flash(f"⚠️ User '{username}' not found", category='warning')
        return redirect(url_for('index'))
    
    # Check if it's a returning user (example: stored in session or database)
    first_visit = session.get(f'first_visit_{username}', True)
    
    if first_visit:
        logger.info(f"First visit from user: {username}")
        flash(f"👋 Welcome, {username}! This is your first visit.", category='info')
        session[f'first_visit_{username}'] = False
    else:
        logger.debug(f"Return visit from user: {username}")
    
    return render_template('user_profile.html', username=username)


@app.route('/process/<operation>')
def process_operation(operation):
    """
    Demonstrate different flash messages based on operation result.
    
    Shows how to use logging + flash together:
    - Log the actual system event (for debugging)
    - Flash the user-friendly message (for UI feedback)
    """
    logger.info(f"Processing operation: {operation}")
    
    operations = {
        'success': ('✅ Operation completed successfully!', 'success'),
        'pending': ('⏳ Operation is processing. Please wait...', 'info'),
        'failed': ('❌ Operation failed. Please try again.', 'error'),
        'timeout': ('⏱️ Operation timed out. Server was busy.', 'warning'),
    }
    
    if operation in operations:
        message, category = operations[operation]
        logger.info(f"Operation '{operation}' - Flash: {message}")
        flash(message, category=category)
    else:
        logger.error(f"Invalid operation requested: {operation}")
        flash("❌ Invalid operation", category='error')
    
    return redirect(url_for('index'))


# ============================================================================
# 5. LOGGING IN ACTION: Error Handling with Logging
# ============================================================================

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    File upload endpoint demonstrating logging + flash integration.
    
    LOGGING HIERARCHY:
    1. DEBUG: "File upload initiated by user X"
    2. INFO: "File saved successfully: filename.txt"
    3. WARNING: "File size larger than recommended"
    4. ERROR: "Disk full - cannot save file"
    5. CRITICAL: "Filesystem corrupted"
    """
    
    logger.debug("File upload request received")
    
    # Check if file in request
    if 'file' not in request.files:
        logger.warning("Upload attempted without file field")
        flash("❌ No file selected", category='error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Check if file has content
    if file.filename == '':
        logger.warning("Upload attempted with empty filename")
        flash("❌ Please select a file", category='error')
        return redirect(url_for('index'))
    
    # Simulate file saving
    try:
        filename = file.filename
        logger.info(f"Attempting to save file: {filename}")
        
        # Simulate processing
        if filename.endswith('.txt'):
            logger.debug(f"File type verified: .txt - proceeding with save")
            # file.save(f"uploads/{filename}")
            logger.info(f"File saved successfully: {filename} (size: ~{len(filename)} bytes)")
            flash(f"✅ File '{filename}' uploaded successfully!", category='success')
        else:
            logger.warning(f"Unsupported file type: {filename.split('.')[-1]}")
            flash("❌ Only .txt files allowed", category='error')
        
        return redirect(url_for('index'))
    
    except PermissionError:
        logger.error(f"Permission denied saving file: {filename}")
        flash("❌ Server permission error", category='error')
        return redirect(url_for('index'))
    except IOError as e:
        logger.error(f"IO Error saving file: {filename} - {str(e)}", exc_info=True)
        flash("❌ Disk error - please try again", category='error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.critical(f"Unexpected error in upload: {str(e)}", exc_info=True)
        flash("❌ Server error - please contact support", category='error')
        return redirect(url_for('index'))


# ============================================================================
# 6. LOGGING DIFFERENT LEVELS
# ============================================================================

@app.route('/debug/<level>')
def test_logging(level):
    """
    Test different logging levels.
    
    Access endpoints to see logs:
    - /debug/debug → Shows DEBUG level
    - /debug/info → Shows INFO level
    - /debug/warning → Shows WARNING level
    - /debug/error → Shows ERROR level
    - /debug/critical → Shows CRITICAL level
    """
    
    test_message = f"Test message for {level} level"
    
    if level == 'debug':
        logger.debug(test_message)
        flash("📝 Debug log created (check console/logs)", category='info')
    elif level == 'info':
        logger.info(test_message)
        flash("ℹ️ Info log created", category='info')
    elif level == 'warning':
        logger.warning(test_message)
        flash("⚠️ Warning log created", category='warning')
    elif level == 'error':
        logger.error(test_message)
        flash("❌ Error log created", category='error')
    elif level == 'critical':
        logger.critical(test_message)
        flash("🚨 Critical log created", category='error')
    else:
        flash("❌ Unknown log level", category='error')
    
    return redirect(url_for('index'))


# ============================================================================
# 7. ERROR HANDLERS WITH LOGGING
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 errors gracefully with logging and flash.
    
    This demonstrates:
    - Logging security events (attempted access to non-existent pages)
    - User-friendly error messages
    """
    logger.warning(f"404 Error: User accessed non-existent page: {request.path}")
    flash("❌ Page not found", category='error')
    return redirect(url_for('index')), 404


@app.errorhandler(500)
def internal_error(e):
    """
    Handle 500 errors (server crashes) with logging.
    
    CRITICAL: Always log 500 errors!
    These indicate serious problems that need attention.
    """
    logger.critical(f"500 Internal Server Error: {str(e)}", exc_info=True)
    flash("❌ Server error. Our team has been notified.", category='error')
    return redirect(url_for('index')), 500


# ============================================================================
# 8. CONTEXT PROCESSOR (Makes variables available to all templates)
# ============================================================================

@app.context_processor
def inject_now():
    """
    Make current datetime available to all templates without passing it.
    
    Usage in template: {{ now }}
    
    This demonstrates advanced Flask patterns.
    """
    return {'now': datetime.now()}


# ============================================================================
# 9. APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Starting Flask Application")
    logger.info("=" * 70)
    
    # Run Flask development server
    # host='0.0.0.0' = accessible from other machines
    # port=5000 = default Flask port
    # debug=True = auto-reload on code changes, detailed error pages
    app.run(host='0.0.0.0', port=5000, debug=True)

    
