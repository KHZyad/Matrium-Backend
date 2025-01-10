from flask import Blueprint, jsonify, request
from app.models.db import db
from app.models.recipe import Recipe
from app.models.recipe_ingredients import RecipeIngredient
from app.models.product import Product
from datetime import datetime, timezone

recipe_routes = Blueprint('recipes', __name__)

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
                "productName": "Recipe Product",
                "category": "Recipe Category",
                "type": "variable",
                "ingredients": ingredients_list,
                "totalPrice": total_price,
                "dateCreated": recipe.created_at.strftime('%Y-%m-%d')
            })

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Route to add a new recipe
@recipe_routes.route('/addRecipe', methods=['POST'])
def add_recipe():
    try:
        data = request.json
        name = data.get('name')
        description = data.get('productName')  # Assuming this maps to description
        created_by = 1  # Assuming the user ID is 1, adjust as necessary
        ingredients = data.get('ingredients')

        if not name or not description or not ingredients:
            return jsonify({"error": "Missing required fields."}), 400

        new_recipe = Recipe(name=name, description=description, created_by=created_by)
        db.session.add(new_recipe)
        db.session.commit()

        for ingredient in ingredients:
            product_name = ingredient.get('name')
            quantity = ingredient.get('quantity')
            price = ingredient.get('price')

            product = db.session.query(Product).filter_by(product_name=product_name).first()
            if not product:
                return jsonify({"error": f"Product {product_name} not found."}), 404

            new_recipe_ingredient = RecipeIngredient(
                recipe_id=new_recipe.recipe_id,
                product_id=product.product_id,
                quantity=quantity
            )
            db.session.add(new_recipe_ingredient)

        db.session.commit()

        return jsonify({"message": "Recipe added successfully.", "recipe_id": new_recipe.recipe_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

# Route to use a recipe and update stock
@recipe_routes.route('/useRecipe/<int:recipe_id>', methods=['POST'])
def use_recipe(recipe_id):
    try:
        recipe = db.session.query(Recipe).filter_by(recipe_id=recipe_id).first()
        if not recipe:
            return jsonify({"error": "Recipe not found."}), 404

        ingredients = db.session.query(RecipeIngredient).filter_by(recipe_id=recipe_id).all()
        total_price = 0

        for ingredient in ingredients:
            product = db.session.query(Product).filter_by(product_id=ingredient.product_id).first()
            if product.quantity < ingredient.quantity:
                return jsonify({"error": f"Not enough stock for product {product.product_name}."}), 400

            product.quantity -= ingredient.quantity
            total_price += ingredient.quantity * product.unit_price

        new_product = Product(
            product_name=recipe.name,
            unit_price=total_price,
            quantity=1,
            supplier="The Factory"
        )
        db.session.add(new_product)
        db.session.commit()

        return jsonify({"message": "Recipe used successfully, new product added.", "new_product_id": new_product.product_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
