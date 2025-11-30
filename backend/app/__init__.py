from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_caching import Cache
from redis import Redis
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
redis_client = Redis()
cache = Cache()

celery = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # ✅ CRITICAL: Enable CORS for Vue.js frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",      # Vite dev server
                "http://127.0.0.1:5173",      # Alternate localhost
                "http://localhost:5000",      # Same origin (optional)
                "http://127.0.0.1:5000"       # Alternate same origin
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "X-Requested-With",
                "Accept",
                "Origin"
            ],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    cache.init_app(app)
    
    # Initialize Redis
    try:
        redis_client.from_url(app.config['REDIS_URL'])
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {e}")
    
    # Initialize Celery
    global celery
    from app.celery_config import make_celery
    celery = make_celery(app)
    
    # ✅ Register blueprints - THIS MUST BE INSIDE create_app()
    with app.app_context():
        from app.routes import auth, admin, doctor, patient
        app.register_blueprint(auth.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(doctor.bp)
        app.register_blueprint(patient.bp)
    
    # ✅ Add a health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'ok', 'message': 'Hospital Management System API is running'}, 200
    
    # ✅ Handle OPTIONS requests globally
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    return app

def create_celery_app(app=None):
    if app is None:
        app = create_app()
    
    from app.celery_config import make_celery
    return make_celery(app)