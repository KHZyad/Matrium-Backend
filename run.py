from flask import Flask
from flask_cors import CORS
from app.models.db import db, init_db 
from app.routes.recipe_routes import recipe_routes
from app.routes.product_routes import product_bp as product_routes
from app.routes.user_routes import user_bp as user_routes

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://avnadmin:AVNS_64D7XhVDVS5mweyqAHs@mysql-615390b-matrium-24.h.aivencloud.com:21017/mrp'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

# Initialize the database
init_db(app)

# Register blueprints
app.register_blueprint(recipe_routes, url_prefix='/')
app.register_blueprint(product_routes, url_prefix='/')
app.register_blueprint(user_routes, url_prefix='/')

@app.route('/')
def home():
    return "Welcome to the Flask App!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
