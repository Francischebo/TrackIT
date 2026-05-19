import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text as sa_text
import shutil
import os as _os

db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()

# Rate Limiting
storage_uri = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["200 per day", "50 per hour"],
)


def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    from config import config_by_name

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    
    # Configure SQLite to use WAL mode and busy timeout to prevent "database is locked" errors
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if type(dbapi_connection).__name__ == "Connection": # sqlite3.Connection
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=15000") # Wait 15 seconds for a lock
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            except Exception:
                pass

    login_manager.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", "*"),
        allow_headers=app.config.get(
            "CORS_HEADERS", "Content-Type,Authorization"
        ).split(","),
        supports_credentials=True,
    )

    login_manager.login_view = "auth.login"

    with app.app_context():
        from app.models import token, user

        @jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
            jti = jwt_payload["jti"]
            return (
                token.TokenBlacklist.query.filter_by(jti=jti).first()
                is not None
            )

        @login_manager.user_loader
        def load_user(user_id):
            return user.User.query.get(int(user_id))

        # Register blueprints (use relative imports to avoid import-resolution issues)
        import importlib

        def _import_bp(module_name: str):
            # Ensure any stray 'app' module is a proper package; if not, reload it
            import sys
            if "app" in sys.modules and not getattr(sys.modules["app"], "__path__", None):
                del sys.modules["app"]

            pkg_candidates = [__package__ or "app", "app"]
            last_exc = None
            for pkg in pkg_candidates:
                try:
                    mod = importlib.import_module(f"{pkg}.blueprints.{module_name}")
                    return getattr(mod, f"{module_name}_bp")
                except Exception as e:
                    last_exc = e
            # If all attempts failed, raise the last exception for visibility
            raise last_exc

        assets_bp = _import_bp("assets")
        audit_bp = _import_bp("audit")
        auth_bp = _import_bp("auth")
        departments_bp = _import_bp("departments")
        inventory_bp = _import_bp("inventory")
        transfers_bp = _import_bp("transfers")
        tracking_bp = _import_bp("tracking")
        restock_bp = _import_bp("restock")
        analytics_bp = _import_bp("analytics")
        reports_bp = _import_bp("reports")
        warehouses_bp = _import_bp("warehouses")
        settings_bp = _import_bp("settings")
        search_bp = _import_bp("search")

        users_bp = _import_bp("users")

        app.register_blueprint(users_bp, url_prefix="/api/users")

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(assets_bp, url_prefix="/api/assets")
        app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
        app.register_blueprint(departments_bp, url_prefix="/api/departments")
        app.register_blueprint(transfers_bp, url_prefix="/api/transfers")
        app.register_blueprint(tracking_bp, url_prefix="/api/tracking")
        app.register_blueprint(restock_bp, url_prefix="/api/restock")
        app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
        app.register_blueprint(audit_bp, url_prefix="/api/audit")
        app.register_blueprint(warehouses_bp, url_prefix="/api/warehouses")
        app.register_blueprint(reports_bp, url_prefix="/api/reports")
        app.register_blueprint(settings_bp, url_prefix="/api/settings")
        app.register_blueprint(search_bp, url_prefix="/api/search")

        # Health check
        @app.route("/health")
        def health_check():
            health = {"status": "healthy", "services": {}}

            # DB Check (use SQLAlchemy text)
            try:
                db.session.execute(sa_text("SELECT 1"))
                health["services"]["database"] = "up"
            except Exception as e:
                app.logger.error(f"Health DB check failed: {str(e)}")
                health["services"]["database"] = "down"
                health["status"] = "unhealthy"

            # Disk Space Check (platform-safe root)
            try:
                root_path = _os.path.abspath(_os.sep)
                total, used, free = shutil.disk_usage(root_path)
                health["system"] = {
                    "disk_free_gb": round(free / (2**30), 2),
                    "disk_total_gb": round(total / (2**30), 2),
                }
                if free < (2**30):  # Less than 1GB
                    health["status"] = "degraded"
            except Exception as e:
                app.logger.warning(f"Disk usage check skipped: {e}")
                health.setdefault("system", {})["disk_check"] = "unavailable"

            return jsonify(health), (
                200 if health["status"] != "unhealthy" else 503
            )

        @app.route("/", methods=["GET"])
        def index():
            """Root endpoint providing basic API information."""
            return (
                jsonify(
                    {
                        "service": "Assets Inventory API",
                        "status": "running",
                        "health": "/health",
                        "endpoints": [
                            "/api/users",
                            "/api/auth",
                            "/api/assets",
                            "/api/inventory",
                        ],
                    }
                ),
                200,
            )

        # Multi-tenant Schema Isolation
        from app.tenant_utils import set_tenant_schema

        @app.before_request
        def handle_tenant_isolation():
            """Switch database schema based on the authenticated user's organization."""
            # Skip for non-API or public routes
            if request.path.startswith('/static') or request.path in ['/health', '/', '/api/auth/login', '/api/auth/register-org']:
                return

            try:
                # Check for JWT and extract organization context
                verify_jwt_in_request(optional=True)
                claims = get_jwt()
                if claims and 'organisation_id' in claims:
                    set_tenant_schema(claims['organisation_id'])
            except Exception as e:
                # Log but don't block; actual auth decorators will handle errors
                app.logger.debug(f"Tenant isolation context skipped: {str(e)}")

        @app.after_request
        def normalize_api_responses(response):
            """Ensure all JSON responses have a consistent format and return 200 OK."""
            if response.is_json:
                try:
                    data = response.get_json()
                    
                    # If it's already an error (from our error handlers), it will have success: False
                    if isinstance(data, dict):
                        # Determine success based on status code
                        is_success = 200 <= response.status_code < 300
                        
                        if 'success' not in data:
                            data['success'] = is_success
                        
                        # Add the original status code
                        if 'status_code' not in data:
                            data['status_code'] = response.status_code
                        
                        response.set_data(jsonify(data).data)
                except Exception:
                    pass
                
                # Force HTTP 200 OK as requested
                response.status_code = 200
            
            return response

        # Security Headers — Enforce strict enterprise standards
        csp = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
            'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            'font-src': ["'self'", "https://fonts.gstatic.com"],
            'img-src': ["'self'", "data:", "https://*", "blob:"],
            'connect-src': ["'self'", "http://localhost:5000", "ws://localhost:5000", "https://*"],
        }
        
        Talisman(
            app,
            content_security_policy=csp,
            force_https=(config_name == 'production'), 
            strict_transport_security=True, 
            session_cookie_secure=(config_name == 'production'),
            session_cookie_http_only=True,
            referrer_policy='strict-origin-when-cross-origin'
        )

        # Register error handlers
        from app.errors import register_error_handlers
        from app.logging_utils import configure_logging

        register_error_handlers(app)
        configure_logging(app)

        # db.create_all() # Moved to migrations

    return app
