from flask import Blueprint, request, jsonify
from app.models.product import Product
from app.models.db import db
from sqlalchemy import func

product_bp = Blueprint('product', __name__)

# Get all products
@product_bp.route('/getProduct', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_formatted_dict() for product in products]), 200


# Create a product
@product_bp.route('/createProduct', methods=['POST'])
def create_product():
    data = request.json
    product = Product(
        product_name=data['product_name'],
        category=data['category'],
        qty_purchased=data['qty_purchased'],
        unit_price=data['unit_price'],
        total_amount=data['qty_purchased'] * data['unit_price'],
        supplier=data['supplier'],
        image=data.get('image'),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "Product created successfully"}), 201

# Update a product
@product_bp.route('/updateProduct', methods=['PUT'])
def update_product():
    data = request.json
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({"message": "Product not found"}), 404

    product.product_name = data['product_name']
    product.category = data['category']
    product.qty_purchased = data['qty_purchased']
    product.unit_price = data['unit_price']
    product.total_amount = data['qty_purchased'] * data['unit_price']
    product.supplier = data['supplier']
    product.status = data['status']
    product.image = data.get('image')

    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200

# Delete a product
@product_bp.route('/deleteProduct', methods=['DELETE'])
def delete_product():
    data = request.json
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({"message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200
@product_bp.route('/analytics', methods=['GET'])
def get_analytics():
    try:
        # Define your thresholds
        low_stock_threshold = 10  # Example: Products with qty_purchased < 10 are considered low in stock

        # Total categories with more than last year (assuming you have a comparison mechanism)
        total_categories_more_than_last_year = db.session.query(Product.category).filter(
            Product.total_amount > Product.last_year_amount  # Assuming you track `last_year_amount`
        ).distinct().count()

        # Total items with positive total_amount
        total_items = db.session.query(Product).filter(Product.total_amount > 0).count()

        # Total item cost
        total_item_cost = db.session.query(func.sum(Product.total_amount)).scalar() or 0

        # Low stock items
        low_stock_items = db.session.query(Product).filter(Product.qty_purchased < low_stock_threshold).count()

        # Out of stock items
        out_of_stock_items = db.session.query(Product).filter(Product.qty_purchased <= 0).count()

        return jsonify({
            "categories_more_than_last_year": total_categories_more_than_last_year,
            "total_items": total_items,
            "total_item_cost": total_item_cost,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


