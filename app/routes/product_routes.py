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
    try:
        data = request.json
        
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
            
            # Calculate weighted average unit price
            total_qty = existing_product.qty_purchased + new_qty
            weighted_unit_price = (
                (existing_product.unit_price * existing_product.qty_purchased) +
                (new_unit_price * new_qty)
            ) / total_qty
            
            # Update product details
            existing_product.qty_purchased = total_qty
            existing_product.unit_price = weighted_unit_price
            existing_product.total_amount = total_qty * weighted_unit_price
            
            # Update status based on new quantity
            if total_qty == 0:
                existing_product.status = "Out of stock"
            elif total_qty <= 10:
                existing_product.status = "Low in stock"
            else:
                existing_product.status = "Available"
            
            db.session.commit()
            return jsonify({"message": "Product updated successfully"}), 200
        
        else:
            # Create new product
            qty_purchased = data['qty_purchased']
            unit_price = data['unit_price']
            
            # Determine product status
            if qty_purchased == 0:
                status = "Out of stock"
            elif qty_purchased <= 10:
                status = "Low in stock"
            else:
                status = "Available"
            
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
        return jsonify({"error": str(e)}), 500


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
        low_stock_threshold = 10

        # Total unique categories
        total_categories = db.session.query(Product.category).distinct().count()

        # Total items (products with total_amount > 0)
        total_items = db.session.query(Product).filter(Product.total_amount > 0).count()

        # Total item cost
        total_item_cost = db.session.query(func.sum(Product.total_amount)).scalar() or 0

        # Low stock items
        low_stock_items = db.session.query(Product).filter(Product.qty_purchased < low_stock_threshold).count()

        # Out of stock items
        out_of_stock_items = db.session.query(Product).filter(Product.qty_purchased <= 0).count()

        return jsonify({
            "total_categories": total_categories,
            "total_items": total_items,
            "total_item_cost": total_item_cost,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



