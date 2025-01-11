from flask import Blueprint, request, jsonify
from app.models.product import Product
from app.models.db import db
from sqlalchemy import func
import traceback

product_bp = Blueprint('product', __name__)

# Utility function to calculate the weighted average
def calculate_weighted_average(existing_qty, existing_price, new_qty, new_price):
    if existing_qty + new_qty == 0:
        return 0  # Avoid division by zero
    return ((existing_price * existing_qty) + (new_price * new_qty)) / (existing_qty + new_qty)

# Function to decide the status based on stock level
def decide_status(qty_purchased):
    if qty_purchased == 0:
        return "Out of Stock"
    elif qty_purchased < 10:
        return "Low in Stock"
    else:
        return "Available"

# Endpoint to retrieve all products
@product_bp.route('/getProduct', methods=['GET'])
def get_products():
    try:
        # Retrieve all products from the database
        products = Product.query.all()
        return jsonify({
            "items": [product.to_formatted_dict() for product in products]
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "An error occurred while retrieving products."}), 500

# Endpoint to create or update a product
@product_bp.route('/createProduct', methods=['POST'])
def create_product():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON payload"}), 400

        data = request.json
        required_fields = ['product_name', 'category', 'qty_purchased', 'unit_price', 'supplier']
        
        # Validate required fields
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Check if the product exists
        existing_product = Product.query.filter_by(
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
            existing_product.status = decide_status(total_qty)  # Set status based on stock level

            db.session.commit()
            return jsonify({"message": "Product updated successfully"}), 200

        else:
            # Create new product
            qty_purchased = data['qty_purchased']
            unit_price = data['unit_price']

            # Create the product with the decided status
            product = Product(
                product_name=data['product_name'],
                category=data['category'],
                qty_purchased=qty_purchased,
                unit_price=unit_price,
                total_amount=qty_purchased * unit_price,
                supplier=data['supplier'],
                image=data.get('image'),  # Optional
                status=decide_status(qty_purchased)  # Set status based on stock level
            )
            db.session.add(product)
            db.session.commit()
            return jsonify({"message": "Product created successfully"}), 201

    except Exception as e:
        traceback.print_exc()  # Log the exception
        return jsonify({"error": "Error while processing product creation", "details": str(e)}), 500

# Endpoint to get stock updates
@product_bp.route('/stockUpdates', methods=['GET'])
def get_stock_updates():
    try:
        # Retrieve all products to get their names and quantities
        products = Product.query.all()

        # Prepare the labels (product names) and stock levels (quantities)
        labels = [product.product_name for product in products]
        stock_levels = [product.qty_purchased for product in products]

        return jsonify({
            "stockUpdates": {
                "labels": labels,
                "stockLevels": stock_levels
            }
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Financial analytics endpoint
@product_bp.route('/finances', methods=['GET'])
def get_financial_data():
    try:
        # Define the months
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        expense_data = []

        # Query expenses for each month
        for month in range(1, 13):
            expenses = db.session.query(
                func.sum(Product.unit_price * Product.qty_purchased)
            ).filter(func.extract('month', Product.last_updated) == month).scalar() or 0
            expense_data.append(expenses)

        return jsonify({
            "finances": {
                "labels": months,
                "expenses": expense_data
            }
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Error processing financial data.", "details": str(e)}), 500
