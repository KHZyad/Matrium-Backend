from app.models.db import db
from datetime import datetime, timezone

class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipe_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum('fixed', 'variable'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    user = db.relationship('User', backref='recipes')
