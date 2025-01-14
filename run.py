from flask import Flask
from flask_cors import CORS
from app.models.db import db, init_db 
from app.routes.recipe_routes import recipe_routes
from app.routes import product_routes
# hope it will work


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 


app.config['SQLALCHEMY_DATABASE_URI'] = ('mysql+pymysql://avnadmin:AVNS_64D7XhVDVS5mweyqAHs@mysql-615390b-matrium-24.h.aivencloud.com:21017/mrp' )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

init_db(app)

app.register_blueprint(recipe_routes, url_prefix='/')
app.register_blueprint(product_routes, url_prefix='/')

@app.route('/')
def home():
    return "Matrium!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
