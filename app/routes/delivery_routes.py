from flask import Blueprint, jsonify, request
from app.models.db import db
from app.models.delivery import Delivery, DeliveryProduct
from app.models.product import Product
from datetime import datetime
import traceback

delivery_routes = Blueprint('delivery', __name__)

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
