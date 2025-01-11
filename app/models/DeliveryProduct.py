from app.models.db import db
#DeliveryProduct

class DeliveryProduct(db.Model):
    __tablename__ = 'delivery_product'

    delivery_id = db.Column(db.BigInteger, db.ForeignKey('delivery.delivery_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('stock.product_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='delivery_products')
