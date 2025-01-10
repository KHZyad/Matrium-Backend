from flask import Blueprint, jsonify, request
from app.models.db import db
from app.models.recipe import Recipe
from app.models.recipe_ingredients import RecipeIngredient
from app.models.product import Product
from datetime import datetime

recipe_routes = Blueprint('recipes', __name__)

def validate_recipe_data(data):
    """Validate the incoming recipe data."""
    required_fields = ['name', 'productName', 'type', 'ingredients']
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing required field: {field}"
    return True, None

def create_recipe(name, description, date_created):
    """Create a new Recipe instance."""
    return Recipe(
        name=name,
        description=description,
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
    total_price = sum(float(ing['price']) for ing in ingredients)
    total_quantity = sum(float(ing['quantity']) for ing in ingredients)
    return total_price, total_quantity

def create_final_product(product_name, unit_price):
    """Create a new Product instance for the final product."""
    return Product(
        product_name=product_name,
        category="Final Material",
        unit_price=unit_price,
        supplier="The Factory",
        quantity=0  # Initial quantity for the new product
    )

@recipe_routes.route('/addRecipe', methods=['POST'])
def add_recipe():
    try:
        data = request.json
        is_valid, error_message = validate_recipe_data(data)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        name = data['name']
        product_name = data['productName']
        recipe_type = data['type']
        ingredients = data['ingredients']
        date_created = data.get('dateCreated', datetime.utcnow().strftime('%Y-%m-%d'))

        new_recipe = create_recipe(name, recipe_type, date_created)
        db.session.add(new_recipe)
        db.session.commit()  # Commit to get the recipe_id

        for ingredient in ingredients:
            new_recipe_ingredient = create_recipe_ingredient(new_recipe.recipe_id, ingredient)
            db.session.add(new_recipe_ingredient)

        total_price, total_quantity = calculate_total_price_and_quantity(ingredients)
        unit_price = total_price / total_quantity if total_quantity else 0
        final_product = create_final_product(product_name, unit_price)
        db.session.add(final_product)

        db.session.commit()

        return jsonify({"message": "Recipe added successfully.", "recipe_id": new_recipe.recipe_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Route to fetch all recipes
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
                "description": recipe.description,
                "ingredients": ingredients_list,
                "totalPrice": total_price,
                "dateCreated": recipe.created_at.strftime('%Y-%m-%d')
            })

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Route to delete a recipe
@recipe_routes.route('/deleteRecipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    try:
        recipe = db.session.query(Recipe).filter_by(recipe_id=recipe_id).first()
        
        if not recipe:
            return jsonify({"error": "Recipe not found."}), 404

        db.session.query(RecipeIngredient).filter_by(recipe_id=recipe_id).delete()
        db.session.delete(recipe)
        db.session.commit()

        return jsonify({"message": "Recipe deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route to use a recipe
@recipe_routes.route('/useRecipe/<int:recipe_id>', methods=['POST'])
def use_recipe(recipe_id):
    try:
        quantity_to_produce = request.json.get('quantity', 1)
        
        recipe = db.session.query(Recipe).filter_by(recipe_id=recipe_id).first()
        if not recipe:
            return jsonify({"error": "Recipe not found."}), 404

        ingredients = (
            db.session.query(RecipeIngredient, Product)
            .join(Product, RecipeIngredient.product_id == Product.product_id)
            .filter(RecipeIngredient.recipe_id == recipe_id)
            .all()
        )

        for ingredient, product in ingredients:
            if product.quantity < ingredient.quantity * quantity_to_produce:
                return jsonify({"error": f"Not enough {product.product_name} in stock."}), 400
            product.quantity -= ingredient.quantity * quantity_to_produce
            db.session.add(product)

        new_product = Product(
            product_name=recipe.name,
            category=recipe.description,
            unit_price=sum([i.quantity * p.unit_price for i, p in ingredients]),
            supplier="The Factory",
            quantity=quantity_to_produce
        )
        db.session.add(new_product)

        db.session.commit()

        return jsonify({"message": "Recipe used successfully, product created.", "product_id": new_product.product_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
