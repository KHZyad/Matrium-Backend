from app.models.db import db

class Product(db.Model):
    __tablename__ = 'stock'

    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    qty_purchased = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    supplier = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Available')
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    image = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "qty_purchased": self.qty_purchased,
            "unit_price": float(self.unit_price),
            "total_amount": float(self.total_amount),
            "supplier": self.supplier,
            "status": self.status,
            "last_updated": self.last_updated,
            "image": self.image,
        }
