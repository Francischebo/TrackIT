"""
PRODUCTION-READY: Updated app/__init__.py with all blueprints registered
Replace existing app/__init__.py with this version
"""

from flask import Flask, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory with enterprise features"""
    app = Flask(__name__)
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # Add JWT config
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'dev-jwt-secret-change-in-production')
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        # Import models to register with SQLAlchemy
        from app.models import user, organization, asset, inventory
        
        @login_manager.user_loader
        def load_user(user_id):
            return user.User.query.get(int(user_id))
        
        # ===== REGISTER BLUEPRINTS =====
        try:
            from app.blueprints.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            print("✓ Auth blueprint registered")
        except Exception as e:
            print(f"⚠ Auth blueprint failed: {e}")
        
        try:
            from app.blueprints.assets import assets_bp
            app.register_blueprint(assets_bp, url_prefix='/api/assets')
            print("✓ Assets blueprint registered")
        except Exception as e:
            print(f"⚠ Assets blueprint failed: {e}")
        
        try:
            from app.blueprints.inventory import inventory_bp
            app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
            print("✓ Inventory blueprint registered")
        except Exception as e:
            print(f"⚠ Inventory blueprint failed: {e}")
        
        try:
            from app.blueprints.reports import reports_bp
            app.register_blueprint(reports_bp, url_prefix='/api/reports')
            print("✓ Reports blueprint registered")
        except Exception as e:
            print(f"⚠ Reports blueprint failed: {e}")
        
        # ===== ERROR HANDLERS =====
        @app.errorhandler(400)
        def bad_request(e):
            return jsonify({
                'error': 'Bad Request',
                'message': str(e.description) if hasattr(e, 'description') else str(e),
                'status': 400
            }), 400
        
        @app.errorhandler(401)
        def unauthorized(e):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required or invalid token',
                'status': 401
            }), 401
        
        @app.errorhandler(403)
        def forbidden(e):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Insufficient permissions for this resource',
                'status': 403
            }), 403
        
        @app.errorhandler(404)
        def not_found(e):
            return jsonify({
                'error': 'Not Found',
                'message': 'Resource not found',
                'status': 404
            }), 404
        
        @app.errorhandler(409)
        def conflict(e):
            return jsonify({
                'error': 'Conflict',
                'message': str(e.description) if hasattr(e, 'description') else 'Resource conflict',
                'status': 409
            }), 409
        
        @app.errorhandler(500)
        def internal_error(e):
            db.session.rollback()
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status': 500
            }), 500
        
        # ===== REQUEST/RESPONSE LOGGING =====
        @app.before_request
        def before_request():
            g.start_time = datetime.utcnow()
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                elapsed = (datetime.utcnow() - g.start_time).total_seconds()
                response.headers['X-Response-Time'] = str(elapsed)
            return response
        
        # ===== HEALTH CHECK =====
        @app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }), 200
        
        # Create database tables
        db.create_all()
        print("✓ Database tables initialized")
    
    return app
