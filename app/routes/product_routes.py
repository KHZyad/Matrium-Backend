from flask import Blueprint, request, jsonify
from app.models.product import Product
from app.models.db import db
from sqlalchemy import func
import traceback
from app.models.delivery import Delivery, DeliveryProduct
from datetime import datetime
#hope it will work


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

# Endpoint to get analytics data
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


# Helper function to validate delivery data
def validate_delivery_data(data):
    required_fields = ['orderId', 'customerName', 'deliveryAddress', 'deliveryDate', 'status', 'deliveryType', 'products']
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing required field: {field}"
    return True, None

# Create Delivery
@delivery_routes.route('/createDelivery', methods=['POST'])
def create_delivery():
    try:
        data = request.json
        is_valid, error_message = validate_delivery_data(data)
        if not is_valid:
            return jsonify({"status": "error", "message": error_message}), 400

        delivery = Delivery(
            order_id=data['orderId'],
            customer_name=data['customerName'],
            delivery_address=data['deliveryAddress'],
            delivery_date=datetime.strptime(data['deliveryDate'], '%Y-%m-%d'),
            status=data['status'],
            delivery_type=data['deliveryType']
        )
        db.session.add(delivery)
        db.session.flush()  # Generate delivery_id

        for product_data in data['products']:
            product = Product.query.get(product_data['id'])
            if not product:
                return jsonify({"status": "error", "message": f"Product ID {product_data['id']} not found"}), 404

            if product.qty_purchased < product_data['quantity']:
                return jsonify({"status": "error", "message": f"Insufficient stock for product {product.product_name}"}), 400

            product.qty_purchased -= product_data['quantity']
            db.session.add(product)

            delivery_product = DeliveryProduct(
                delivery_id=delivery.delivery_id,
                product_id=product.product_id,
                quantity=product_data['quantity']
            )
            db.session.add(delivery_product)

        db.session.commit()
        return jsonify({"status": "success", "message": "Delivery created successfully.", "delivery_id": delivery.delivery_id}), 201
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Get all deliveries
@delivery_routes.route('/getDeliveries', methods=['GET'])
def get_deliveries():
    try:
        deliveries = Delivery.query.all()
        result = []
        for delivery in deliveries:
            products = DeliveryProduct.query.filter_by(delivery_id=delivery.delivery_id).all()
            product_list = []
            for dp in products:
                product = Product.query.get(dp.product_id)
                product_list.append({
                    "id": product.product_id,
                    "name": product.product_name,
                    "quantity": dp.quantity
                })

            result.append({
                "deliveryId": delivery.delivery_id,
                "orderId": delivery.order_id,
                "customerName": delivery.customer_name,
                "deliveryAddress": delivery.delivery_address,
                "deliveryDate": delivery.delivery_date.strftime('%Y-%m-%d'),
                "status": delivery.status,
                "deliveryType": delivery.delivery_type,
                "products": product_list
            })

        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Update Delivery
@delivery_routes.route('/updateDelivery/<int:delivery_id>', methods=['PUT'])
def update_delivery(delivery_id):
    try:
        data = request.json
        delivery = Delivery.query.get(delivery_id)
        if not delivery:
            return jsonify({"status": "error", "message": "Delivery not found"}), 404

        delivery.customer_name = data.get('customerName', delivery.customer_name)
        delivery.delivery_address = data.get('deliveryAddress', delivery.delivery_address)
        delivery.delivery_date = datetime.strptime(data['deliveryDate'], '%Y-%m-%d') if data.get('deliveryDate') else delivery.delivery_date
        delivery.status = data.get('status', delivery.status)
        delivery.delivery_type = data.get('deliveryType', delivery.delivery_type)

        db.session.commit()
        return jsonify({"status": "success", "message": "Delivery updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Delete Delivery
@delivery_routes.route('/deleteDelivery/<int:delivery_id>', methods=['DELETE'])
def delete_delivery(delivery_id):
    try:
        delivery = Delivery.query.get(delivery_id)
        if not delivery:
            return jsonify({"status": "error", "message": "Delivery not found"}), 404

        # Restore stock quantities
        products = DeliveryProduct.query.filter_by(delivery_id=delivery_id).all()
        for dp in products:
            product = Product.query.get(dp.product_id)
            product.qty_purchased += dp.quantity
            db.session.add(product)

        DeliveryProduct.query.filter_by(delivery_id=delivery_id).delete()
        db.session.delete(delivery)

        db.session.commit()
        return jsonify({"status": "success", "message": "Delivery deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
