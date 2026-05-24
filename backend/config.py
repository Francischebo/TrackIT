import os
from datetime import timedelta


class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "None"
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_REFRESH_CSRF_HEADER_NAME = "X-CSRF-TOKEN"

    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"

    # CORS
    CORS_HEADERS = "Content-Type,Authorization"
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5000"
    ).split(",")

    # Security
    BCRYPT_LOG_ROUNDS = 12

    # QR tracking
    TRACKING_PUBLIC_URL = os.environ.get(
        "TRACKING_PUBLIC_URL", "http://localhost:5173/tracking"
    )
    QR_PAYLOAD_TTL_DAYS = int(os.environ.get("QR_PAYLOAD_TTL_DAYS", "365"))
    SCAN_DEDUP_SECONDS = int(os.environ.get("SCAN_DEDUP_SECONDS", "30"))

    # SQLAlchemy engine options - helpful for PostgreSQL in production
    # Note: client_encoding is PostgreSQL-specific, only set for PostgreSQL
    _db_url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_URL_PROD")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    # Only add PostgreSQL-specific options when using PostgreSQL
    if _db_url and _db_url.startswith("postgresql://"):
        SQLALCHEMY_ENGINE_OPTIONS["client_encoding"] = "utf8"
        # Avoid long blocking on initial connect; set a connect timeout
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"connect_timeout": 10}



class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///trackit_dev.db"
    )
    SESSION_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Lax"

    # Development CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:8080",
    ]


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    
    # Disable CSRF checks for cookie-based JWT in cross-site environments.
    # This prevents 401 on safe session checks like GET /api/auth/me when
    # the frontend cannot reliably emit X-CSRF-TOKEN.
    JWT_COOKIE_CSRF_PROTECT = False
    

    
    # Secure database URI with SSL requirement if PostgreSQL
    _db_url = os.environ.get("DATABASE_URL_PROD") or os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgresql://") and "sslmode=" not in _db_url:
        _db_url += "?sslmode=require"
    SQLALCHEMY_DATABASE_URI = _db_url

    # Production security
    SESSION_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "None"
    
    _cors_env = os.environ.get("CORS_ORIGINS", "").strip()
    CORS_ORIGINS = (
        [o.strip() for o in _cors_env.split(",") if o.strip()]
        if _cors_env
        else [
            "https://track-it-eta-one.vercel.app",
            "https://track-it-gamma-blue.vercel.app",
        ]
    )


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    SECRET_KEY = "test-secret-key"
    JWT_SECRET_KEY = "test-jwt-secret-key"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
