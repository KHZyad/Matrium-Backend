from flask import Blueprint, jsonify, request
from app.models.db import db
from app.models.recipe import Recipe
from app.models.recipe_ingredients import RecipeIngredient
from app.models.product import Product
from datetime import datetime
import traceback

# Define the Blueprint
recipe_routes = Blueprint('recipes', __name__)

# Helper functions
def validate_recipe_data(data):
    """Validate the incoming recipe data."""
    required_fields = ['name', 'productName', 'type', 'ingredients', 'totalPrice', 'category']
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing required field: {field}"
    return True, None

def create_recipe(name, recipe_type, product_name, date_created):
    """Create a new Recipe instance."""
    return Recipe(
        name=name,
        type=recipe_type,
        product_name=product_name,
        total_price=0.0,
        created_at=datetime.strptime(date_created, '%Y-%m-%d')
    )

def create_recipe_ingredient(recipe_id, ingredient_data):
    """Create a new RecipeIngredient instance."""
    return RecipeIngredient(
        recipe_id=recipe_id,
        product_id=ingredient_data['stockId'],
        quantity=float(ingredient_data['quantity'])
    )

def calculate_total_price_and_quantity(ingredients):
    """Calculate the total price and total quantity of ingredients."""
    total_price = sum(float(ing['price']) * float(ing['quantity']) for ing in ingredients)
    total_quantity = sum(float(ing['quantity']) for ing in ingredients)
    return total_price, total_quantity

def create_final_product(product_name, unit_price, total_price, category):
    """Create a new Product instance for the final product."""
    return Product(
        product_name=product_name,
        category=category,
        qty_purchased=0,  # Default to 0 for the final product
        unit_price=unit_price,
        total_amount=total_price,
        supplier="The Factory",
        status="Available",
        image=None
    )

# Routes
@recipe_routes.route('/addRecipe', methods=['POST'])
def add_recipe():
    try:
        data = request.json
        is_valid, error_message = validate_recipe_data(data)
        if not is_valid:
            return jsonify({"status": "error", "message": error_message}), 400

        name = data['name']
        product_name = data['productName']
        recipe_type = data['type']
        ingredients = data['ingredients']
        date_created = data.get('dateCreated', datetime.utcnow().strftime('%Y-%m-%d'))
        category = data['category']

        # Create the recipe
        new_recipe = create_recipe(name, recipe_type, product_name, date_created)
        db.session.add(new_recipe)
        db.session.commit()  # Commit to get the recipe_id

        # Add ingredients to the recipe
        for ingredient in ingredients:
            new_recipe_ingredient = create_recipe_ingredient(new_recipe.recipe_id, ingredient)
            db.session.add(new_recipe_ingredient)

        # Calculate total price and create the final product
        total_price, total_quantity = calculate_total_price_and_quantity(ingredients)
        unit_price = total_price / total_quantity if total_quantity else 0
        final_product = create_final_product(product_name, unit_price, total_price, category)
        db.session.add(final_product)

        db.session.commit()

        return jsonify({"status": "success", "message": "Recipe added successfully.", "recipe_id": new_recipe.recipe_id}), 201
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@recipe_routes.route('/getRecipes', methods=['GET'])
def get_recipes():
    try:
        recipes = db.session.query(Recipe).order_by(Recipe.created_at.desc()).all()
        result = []

        for recipe in recipes:
            ingredients = (
                db.session.query(RecipeIngredient, Product)
                .join(Product, RecipeIngredient.product_id == Product.product_id)
                .filter(RecipeIngredient.recipe_id == recipe.recipe_id)
                .all()
            )
            ingredients_list = []
            total_price = 0

            for ingredient, product in ingredients:
                ingredient_price = ingredient.quantity * product.unit_price
                total_price += ingredient_price
                ingredients_list.append({
                    "name": product.product_name,
                    "quantity": ingredient.quantity,
                    "unit": product.category,
                    "price": ingredient_price
                })

            result.append({
                "id": recipe.recipe_id,
                "name": recipe.name,
                "type": recipe.type,
                "ingredients": ingredients_list,
                "totalPrice": total_price,
                "dateCreated": recipe.created_at.strftime('%Y-%m-%d')
            })

        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@recipe_routes.route('/deleteRecipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    try:
        recipe = db.session.query(Recipe).filter_by(recipe_id=recipe_id).first()

        if not recipe:
            return jsonify({"status": "error", "message": "Recipe not found."}), 404

        db.session.query(RecipeIngredient).filter_by(recipe_id=recipe_id).delete()
        db.session.delete(recipe)
        db.session.commit()

        return jsonify({"status": "success", "message": "Recipe deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@recipe_routes.route('/useRecipe/<int:recipe_id>', methods=['POST'])
def use_recipe(recipe_id):
    try:
        quantity_to_produce = request.json.get('quantity', 1)
        if quantity_to_produce <= 0:
            return jsonify({"status": "error", "message": "Invalid quantity to produce."}), 400

        recipe = db.session.query(Recipe).filter_by(recipe_id=recipe_id).first()
        if not recipe:
            return jsonify({"status": "error", "message": "Recipe not found."}), 404

        ingredients = (
            db.session.query(RecipeIngredient, Product)
            .join(Product, RecipeIngredient.product_id == Product.product_id)
            .filter(RecipeIngredient.recipe_id == recipe_id)
            .all()
        )

        for ingredient, product in ingredients:
            required_quantity = ingredient.quantity * quantity_to_produce
            if product.qty_purchased < required_quantity:
                return jsonify({"status": "error", "message": f"Not enough {product.product_name} in stock."}), 400
            product.qty_purchased -= required_quantity
            db.session.add(product)

        total_price = sum(ingredient.quantity * product.unit_price for ingredient, product in ingredients)
        unit_price = total_price / quantity_to_produce if quantity_to_produce > 0 else 0

        new_product = Product(
            product_name=recipe.product_name,
            category="Final Material",
            qty_purchased=quantity_to_produce,
            unit_price=unit_price,
            total_amount=total_price,
            supplier="The Factory",
            status="Available"
        )
        db.session.add(new_product)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Recipe used successfully, product created.",
            "product_id": new_product.product_id
        }), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
