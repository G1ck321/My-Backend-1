from flask import jsonify
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    """Custom base exception class"""

    def __init__(self, message, status_code=400, error_type="validation_error"):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.error_type = error_type


class ValidationError(AppError):
    """Input validation errors"""

    def __init__(self, message="Invalid input data"):
        super().__init__(message, 400, "validation_error")


class NotFoundError(AppError):
    """Resource not found"""

    def __init__(self, message="Resource not found"):
        super().__init__(message, 404, "not_found")


class ConflictError(AppError):
    """Duplicate resource errors"""

    def __init__(self, message="Resource Already Exists"):
        super().__init__(message, 409, "conflict")


def register_error_handlers(app):
    """Register all error handlers with the Flask app."""

    @app.errorhandler(AppError)
    def handle_app_error(error):
        """Handle custom application errors"""
        response = jsonify(
            {
                "error": {
                    "type": error.error_type,
                    "message": error.message,
                    "code": error.status_code,
                }
            })
        response.status_code = error.status_code
        return response

    @app.error_handler(404)
    def not_found(error):
        """Handles 404 errors"""
        return jsonify(
            {
                "error": {
                    "type": "not_found",
                    "message": "The requested resource was not found",
                    "code": 404,
                }
            }),404
    @app.error_handler(500)
    def internal_error(error):
        """Handles 500 errors"""
        #log the actual error for debugging
        app.logger.error(f"Internl Server Error: {str(error)}")
        return jsonify(
            {
                "errpor": {
                    "type": "not_found",
                    "message": "The requested resource was not found",
                    "code": 500,
                }
            }),500
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Catch-all for unhandled exceptions"""
        app.logger.error(f"Unhandled exception: {str(error)}")
        return jsonify({
            "error":{
                "type":"server_error",
                "message":"An unexected error occured",
                "code":500
            }
        }),500
        