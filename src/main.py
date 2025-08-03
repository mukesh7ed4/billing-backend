import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.user import db
from src.database_sqlite import init_db

# Import routes
from src.routes.auth import auth_bp
from src.routes.shop import shop_bp
from src.routes.admin import admin_bp
from src.routes.payment import payment_bp
from src.routes.expense import expense_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Load environment variables with defaults
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'billing-system-secret-key-2024')
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'development')
app.config['FLASK_DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# CORS configuration for production
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000,https://your-frontend-domain.vercel.app').split(',')
CORS(app, supports_credentials=True, origins=cors_origins)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(shop_bp, url_prefix='/api/shop')
app.register_blueprint(payment_bp, url_prefix='/api/payment')
app.register_blueprint(expense_bp, url_prefix='/api/expense')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Billing System API is running',
        'version': '2.0.0'
    }), 200

# Root endpoint
@app.route('/api', methods=['GET'])
def api_root():
    """API root endpoint"""
    return jsonify({
        'message': 'Billing System API',
        'version': '2.0.0',
        'endpoints': {
            'auth': '/api/auth',
            'admin': '/api/admin',
            'shop': '/api/shop',
            'payment': '/api/payment'
        }
    }), 200

# Serve frontend files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({'message': 'Frontend not built yet'}), 404

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized access'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden access'}), 403

# For production deployment
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

