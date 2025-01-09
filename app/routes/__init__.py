from flask import Flask
from app.routes.user_routes import user_bp as user_routes
from app.routes.product_routes import product_bp as product_routes
from app.routes.defect_routes import defect_bp as defect_routes
from app.routes.recipe_routes import recipe_routes  # Import the new blueprint

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(user_routes, url_prefix='/users')
    app.register_blueprint(product_routes, url_prefix='/products')
    app.register_blueprint(defect_routes, url_prefix='/defects')
    app.register_blueprint(recipe_routes, url_prefix='/recipes')  # Register the new routes

    return app
