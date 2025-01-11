from app.models.db import db
from datetime import datetime

class Delivery(db.Model):
    __tablename__ = 'delivery'

    delivery_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(255), nullable=False)
    delivery_address = db.Column(db.String(255), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    delivery_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeliveryProduct(db.Model):
    __tablename__ = 'delivery_product'

    delivery_id = db.Column(db.BigInteger, db.ForeignKey('delivery.delivery_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('stock.product_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    delivery = db.relationship('Delivery', backref='products')
    product = db.relationship('Product', backref='deliveries')
