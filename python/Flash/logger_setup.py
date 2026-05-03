"""
========================================================================
logger_setup.py
========================================================================
Centralized Logging Configuration Module

This module demonstrates the professional way to handle logging in Python.
Instead of scattering logging code throughout your app, we configure it
once here and import it everywhere.

ANALOGY: Logger Setup as a Central News Broadcast Station
- Your app = multiple reporters sending stories
- Logger = broadcast station receiving stories from reporters
- Handlers = TV channels, radios, newspapers distributing the stories
- Formatters = how each medium presents the story (headline vs. full article)

WHY SEPARATE FILE?
- Reusability: Multiple files can import this logger
- Consistency: All logs use same format and level
- Maintainability: Change logging behavior in one place
========================================================================
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(app=None, log_level=logging.INFO):
    """
    Configure logging for the Flask application.
    
    PARAMETERS:
        app (Flask app): Optional Flask app instance
        log_level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    RETURNS:
        logging.Logger: Configured logger instance
    
    WHAT THIS DOES:
    ===============
    Sets up THREE logging outputs simultaneously:
    
    1. CONSOLE OUTPUT (Terminal/stdout)
       - Shows logs while you're developing
       - Helps debug in real-time
       - Format: [TIMESTAMP] [LEVEL] [LOGGER_NAME] - [MESSAGE]
    
    2. FILE OUTPUT (logs/app.log)
       - Permanent record of all events
       - Survives application restart
       - Rotates when file gets too big (10MB max)
    
    3. ERROR FILE OUTPUT (logs/errors.log)
       - Only critical errors
       - Separate file for easy filtering
       - Helps identify production issues quickly
    
    WHY THREE OUTPUTS?
    - Console: Immediate feedback during development
    - Main file: Long-term audit trail
    - Error file: Quick access to problems
    """
    
    # Create logger instance with application name
    # The name helps identify where logs come from in production
    logger = logging.getLogger('FlashApp')
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if setup called multiple times
    if logger.hasHandlers():
        return logger
    
    # Create logs directory if it doesn't exist
    # (exist_ok=True prevents error if directory already exists)
    os.makedirs('logs', exist_ok=True)
    
    # ========================================================================
    # 1. CONSOLE HANDLER - Logs appear in terminal while running
    # ========================================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Format for console (colored would be nice, but keeping it simple)
    console_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # ========================================================================
    # 2. FILE HANDLER - Main application log file (rotating)
    # ========================================================================
    # RotatingFileHandler = automatically creates new file when size exceeds limit
    # maxBytes=10MB, backupCount=5 means keep 5 old files (app.log.1, app.log.2, etc.)
    file_handler = RotatingFileHandler(
        filename='logs/app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5  # Keep 5 previous files
    )
    file_handler.setLevel(log_level)
    
    # More detailed format for file (include function name and line number)
    file_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # ========================================================================
    # 3. ERROR FILE HANDLER - Only captures ERROR and CRITICAL levels
    # ========================================================================
    error_handler = RotatingFileHandler(
        filename='logs/errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)  # Only ERROR and above
    
    error_format = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s\nContext: %(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_format)
    logger.addHandler(error_handler)
    
    # If Flask app provided, integrate with Flask's logger
    if app:
        app.logger.addHandler(console_handler)
        app.logger.addHandler(file_handler)
    
    # Log that setup completed
    logger.info("=" * 70)
    logger.info("Logger initialized successfully")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Logs directory: {os.path.abspath('logs')}")
    logger.info("=" * 70)
    
    return logger


# ============================================================================
# LOGGING LEVELS EXPLAINED (in order of severity)
# ============================================================================
"""
1. DEBUG (10): Detailed information, typically of interest only when diagnosing problems.
   Example: "Variable X = 42", "Entering function Y", "Database query took 2ms"
   
2. INFO (20): Confirmation that things are working as expected.
   Example: "Server started", "User logged in", "File uploaded successfully"
   
3. WARNING (30): An indication that something unexpected happened, or may happen.
   Example: "File not found (using default)", "API response slow (>5s)", "Disk space low"
   
4. ERROR (40): A serious problem, something failed.
   Example: "Cannot connect to database", "Invalid user input", "File write failed"
   
5. CRITICAL (50): A very serious error, the program itself may not continue.
   Example: "Out of memory", "Cannot start server", "Configuration file missing"
"""


# ============================================================================
# USAGE EXAMPLE
# ============================================================================
"""
In your app.py:

    from logger_setup import setup_logger
    
    app = Flask(__name__)
    logger = setup_logger(app, log_level=logging.DEBUG)
    
    @app.route('/upload', methods=['POST'])
    def upload():
        logger.debug("Upload request received")
        try:
            # ... process file ...
            logger.info(f"File uploaded successfully: {filename}")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            # exc_info=True includes the full stack trace


LOG OUTPUT EXAMPLES:

Console (what you see while running):
    2024-04-30 14:23:45 - FlashApp - INFO - Server started
    2024-04-30 14:23:46 - FlashApp - DEBUG - Processing user request
    2024-04-30 14:23:47 - FlashApp - INFO - File uploaded successfully

logs/app.log (persistent file):
    2024-04-30 14:23:45 - FlashApp - INFO - [app.py:run:42] - Server started
    2024-04-30 14:23:46 - FlashApp - DEBUG - [routes.py:process:128] - Processing user request
    2024-04-30 14:23:47 - FlashApp - INFO - [routes.py:upload:145] - File uploaded successfully

logs/errors.log (only errors):
    2024-04-30 14:30:12 - ERROR - [routes.py:upload:146] - Upload failed: Disk full
    Context: Traceback (most recent call last):
      File "routes.py", line 145, in upload
        file.save(path)
    IOError: No space left on device
"""
