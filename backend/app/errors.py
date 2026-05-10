import traceback

from flask import current_app, jsonify, request

from app import db
from app.audit_service import AuditService


class APIError(Exception):
    """Base API error class"""

    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


class ValidationError(APIError):
    """Validation error"""

    def __init__(self, message, errors=None):
        super().__init__(message, 400, {"validation_errors": errors})


class AuthenticationError(APIError):
    """Authentication error"""

    def __init__(self, message="Authentication required"):
        super().__init__(message, 401)


class AuthorizationError(APIError):
    """Authorization error"""

    def __init__(self, message="Insufficient permissions"):
        super().__init__(message, 403)


class NotFoundError(APIError):
    """Resource not found error"""

    def __init__(self, message="Resource not found"):
        super().__init__(message, 404)


class ConflictError(APIError):
    """Resource conflict error"""

    def __init__(self, message="Resource conflict"):
        super().__init__(message, 409)


def register_error_handlers(app):
    """Register error handlers for the Flask app"""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        # Log the error
        AuditService.log_user_action(
            action="API_ERROR",
            details={
                "error_type": error.__class__.__name__,
                "message": error.message,
                "status_code": error.status_code,
                "endpoint": request.endpoint,
                "method": request.method,
                "url": request.url,
            },
        )

        response = {
            "success": False,
            "error": error.__class__.__name__,
            "message": error.message,
            "status_code": error.status_code,
        }
        if error.payload:
            response.update(error.payload)

        # Force 200 as requested
        return jsonify(response), 200

    @app.errorhandler(400)
    def handle_bad_request(error):
        AuditService.log_user_action(
            action="BAD_REQUEST",
            details={
                "description": error.description,
                "endpoint": request.endpoint,
                "method": request.method,
            },
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "BadRequest",
                    "message": "Invalid request data",
                    "details": error.description,
                    "status_code": 400
                }
            ),
            200,
        )

    @app.errorhandler(401)
    def handle_unauthorized(error):
        AuditService.log_user_action(
            action="UNAUTHORIZED_ACCESS",
            details={
                "endpoint": request.endpoint,
                "method": request.method,
                "url": request.url,
            },
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Unauthorized", 
                    "message": "Authentication required",
                    "status_code": 401
                }
            ),
            200,
        )

    @app.errorhandler(403)
    def handle_forbidden(error):
        AuditService.log_user_action(
            action="FORBIDDEN_ACCESS",
            details={
                "endpoint": request.endpoint,
                "method": request.method,
                "url": request.url,
            },
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Forbidden", 
                    "message": "Insufficient permissions",
                    "status_code": 403
                }
            ),
            200,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        AuditService.log_user_action(
            action="NOT_FOUND",
            details={
                "endpoint": request.endpoint,
                "method": request.method,
                "url": request.url,
            },
        )
        return (
            jsonify({
                "success": False,
                "error": "NotFound", 
                "message": "Resource not found",
                "status_code": 404
            }),
            200,
        )

    @app.errorhandler(429)
    def handle_rate_limit(error):
        AuditService.log_user_action(
            action="RATE_LIMIT_EXCEEDED",
            details={
                "endpoint": request.endpoint,
                "method": request.method,
                "url": request.url,
            },
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "RateLimitExceeded", 
                    "message": "Too many requests",
                    "status_code": 429
                }
            ),
            200,
        )

    from sqlalchemy.exc import IntegrityError, DataError, OperationalError

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        current_app.logger.warning(f"Database integrity error: {str(error)}")

        message = "A database integrity constraint was violated."
        if "unique" in str(error).lower():
            message = "This record already exists in the system."
        elif "foreign key" in str(error).lower():
            message = "This operation cannot be completed because the record is referenced by other data."

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Conflict", 
                    "message": message, 
                    "status_code": 409
                }
            ),
            200,
        )

    @app.errorhandler(DataError)
    def handle_data_error(error):
        db.session.rollback()
        current_app.logger.warning(f"Database data error: {str(error)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "ValidationError",
                    "message": "The provided data format is invalid for the database.",
                    "status_code": 400,
                }
            ),
            200,
        )

    @app.errorhandler(OperationalError)
    def handle_operational_error(error):
        db.session.rollback()
        current_app.logger.error(f"Database operational error: {str(error)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "ServiceUnavailable",
                    "message": "The database is currently unavailable or busy. Please try again later.",
                    "status_code": 503,
                }
            ),
            200,
        )

    from werkzeug.exceptions import HTTPException

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Catch all standard Flask/Werkzeug HTTP exceptions."""
        AuditService.log_user_action(
            action="HTTP_EXCEPTION",
            details={
                "code": error.code,
                "name": error.name,
                "description": error.description,
                "endpoint": request.endpoint,
                "method": request.method,
            },
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": error.name,
                    "message": error.description,
                    "status_code": error.code
                }
            ),
            200,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Catch any unhandled exceptions
        current_app.logger.error(f"Unexpected error: {traceback.format_exc()}")

        AuditService.log_user_action(
            action="UNEXPECTED_ERROR",
            details={
                "error_type": type(error).__name__,
                "endpoint": request.endpoint,
                "method": request.method,
                "error": "Error details captured in system logs",
            },
        )

        db.session.rollback()

        return (
            jsonify(
                {
                    "success": False,
                    "error": "InternalServerError",
                    "message": "An unexpected system error occurred.",
                    "status_code": 500,
                    "details": str(error) if current_app.debug else None
                }
            ),
            200,
        )
