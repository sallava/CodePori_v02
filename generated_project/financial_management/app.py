from flask import Flask
from config.config import Config
from database.database import init_db
from views.financial_views import financial_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(financial_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)