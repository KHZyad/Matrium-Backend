from app.models.db import db

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.recipe_id'), primary_key=True)  # Composite primary key
    product_id = db.Column(db.Integer, db.ForeignKey('stock.product_id'), primary_key=True)  # Composite primary key
    quantity = db.Column(db.Float, nullable=False)

    recipe = db.relationship('Recipe', backref='ingredients')  
    product = db.relationship('Product', backref='recipe_ingredients')  # Relationship to Product (stock table)
