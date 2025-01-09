from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from app.models.db import db, init_db

def create_app():
   
    app = Flask(__name__)

   
    CORS(app)

   
    app.config.from_object('app.config.Config')

   
    init_db(app)

    
    migrate = Migrate(app, db)

    from app.routes.product_routes import product_bp
    app.register_blueprint(product_bp, url_prefix='/api/product')


    return app