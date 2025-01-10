from flask import Blueprint, request, jsonify
from app.models.product import Product
from app.models.db import db
from sqlalchemy import func
import traceback

product_bp = Blueprint('product', __name__)

def determine_status(qty_purchased):
    if qty_purchased == 0:
        return "Out of stock"
    elif qty_purchased <= 10:
        return "Low in stock"
    return "Available"

def calculate_weighted_average(existing_qty, existing_price, new_qty, new_price):
    if existing_qty + new_qty == 0:
        return 0  # Avoid division by zero
    return ((existing_price * existing_qty) + (new_price * new_qty)) / (existing_qty + new_qty)

# Get all products
@product_bp.route('/getProduct', methods=['GET'])
def get_products():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        products = Product.query.paginate(page=page, per_page=per_page)

        return jsonify({
            "items": [product.to_formatted_dict() for product in products.items],
            "total": products.total,
            "pages": products.pages,
            "current_page": products.page
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Create a product
@product_bp.route('/createProduct', methods=['POST'])
def create_product():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON payload"}), 400

        data = request.json
        required_fields = ['product_name', 'category', 'qty_purchased', 'unit_price', 'supplier']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Check if the product exists (based on productId, product_name, category, and supplier)
        existing_product = Product.query.filter_by(
            product_id=data['product_id'],
            product_name=data['product_name'],
            category=data['category'],
            supplier=data['supplier']
        ).first()

        if existing_product:
            # Update existing product
            new_qty = data['qty_purchased']
            new_unit_price = data['unit_price']

            total_qty = existing_product.qty_purchased + new_qty
            weighted_unit_price = calculate_weighted_average(
                existing_product.qty_purchased,
                existing_product.unit_price,
                new_qty,
                new_unit_price
            )

            existing_product.qty_purchased = total_qty
            existing_product.unit_price = weighted_unit_price
            existing_product.total_amount = total_qty * weighted_unit_price
            existing_product.status = determine_status(total_qty)

            db.session.commit()
            return jsonify({"message": "Product updated successfully"}), 200

        else:
            # Create new product
            qty_purchased = data['qty_purchased']
            unit_price = data['unit_price']

            status = determine_status(qty_purchased)

            product = Product(
                product_id=data['product_id'],
                product_name=data['product_name'],
                category=data['category'],
                qty_purchased=qty_purchased,
                unit_price=unit_price,
                total_amount=qty_purchased * unit_price,
                supplier=data['supplier'],
                image=data.get('image'),
                status=status
            )
            db.session.add(product)
            db.session.commit()
            return jsonify({"message": "Product created successfully"}), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Update a product
@product_bp.route('/updateProduct', methods=['PUT'])
def update_product():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON payload"}), 400

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
        product.status = determine_status(data['qty_purchased'])
        product.image = data.get('image')

        db.session.commit()
        return jsonify({"message": "Product updated successfully"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Delete a product
@product_bp.route('/deleteProduct', methods=['DELETE'])
def delete_product():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON payload"}), 400

        data = request.json
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({"message": "Product not found"}), 404

        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Analytics endpoint
@product_bp.route('/analytics', methods=['GET'])
def get_analytics():
    try:
        low_stock_threshold = 10

        total_categories = db.session.query(Product.category).distinct().count()
        total_items = db.session.query(Product).filter(Product.total_amount > 0).count()
        total_item_cost = db.session.query(func.sum(Product.total_amount)).scalar() or 0
        low_stock_items = db.session.query(Product).filter(Product.qty_purchased < low_stock_threshold).count()
        out_of_stock_items = db.session.query(Product).filter(Product.qty_purchased <= 0).count()

        return jsonify({
            "total_categories": total_categories,
            "total_items": total_items,
            "total_item_cost": total_item_cost,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
