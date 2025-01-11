from app.models.db import db

class Product(db.Model):
    __tablename__ = 'stock'
    
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    qty_purchased = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100), nullable=False)
     status = db.Column(db.String(50), default="In stock")
    image = db.Column(db.String(255))
    last_updated = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def to_formatted_dict(self):
        return {
            "id": str(self.product_id).zfill(2),  # Formats product_id as a two-digit string
            "image": self.image or "src/assets/images/default.png",  # Fallback image if not provided
            "productName": self.product_name,
            "productId": f"ST-{self.product_name[:3].upper()}-{str(self.product_id).zfill(3)}",  # Custom product ID
            "category": self.category,
            "qtyPurchased": f"{self.qty_purchased} pcs",
            "unitPrice": f"{self.unit_price:.2f}",
            "totalAmount": f"{self.total_amount:,.2f}",  # Adds comma separators for thousands
            "supplier": self.supplier,
            "status": self.status
        }
