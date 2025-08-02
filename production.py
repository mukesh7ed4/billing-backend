import os
from src.main import app

if __name__ == "__main__":
    # Production settings
    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # CORS settings for production
    from flask_cors import CORS
    CORS(app, origins=[
        os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
        'https://your-domain.com'  # Replace with your actual domain
    ])
    
    # Run with Gunicorn
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 