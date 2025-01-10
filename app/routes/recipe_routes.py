from flask import Blueprint, jsonify, request
from app.models.db import db
from app.models.user import User  # Assuming you have a User model for created_by
from app.models.recipe import Recipe
from app.models.recipe_ingredients import RecipeIngredient
from app.models.product import Product

recipe_routes = Blueprint('recipes', __name__)

@recipe_routes.route('/getRecipes', methods=['GET'])
def get_recipes():
    try:
        # Fetch all recipes
        recipes = db.session.query(Recipe).join(User).order_by(Recipe.created_at.desc()).all()
        result = []

        for recipe in recipes:
            # Fetch ingredients for each recipe
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
                    "unit": product.category,  # Assuming the product category corresponds to the unit
                    "price": ingredient_price
                })

            result.append({
                "id": recipe.recipe_id,
                "name": recipe.name,
                "productName": "Recipe Product",  # Add logic if this maps to something in your database
                "category": "Recipe Category",  # Add logic if this maps to something in your database
                "type": "variable",  # Assuming this is static for now
                "ingredients": ingredients_list,
                "totalPrice": total_price,
                "dateCreated": recipe.created_at.strftime('%Y-%m-%d')
            })

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@recipe_routes.route('/addRecipe', methods=['POST'])
def add_recipe():
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description')
        created_by = data.get('created_by')
        ingredients = data.get('ingredients')  # List of ingredients from the request body

        if not name or not description or not created_by or not ingredients:
            return jsonify({"error": "Missing required fields."}), 400

        # Add the recipe to the database
        new_recipe = Recipe(name=name, description=description, created_by=created_by)
        db.session.add(new_recipe)
        db.session.commit()

        # Add ingredients to the recipe_ingredients table
        for ingredient in ingredients:
            product_id = ingredient.get('product_id')
            quantity = ingredient.get('quantity')

            if not product_id or not quantity:
                return jsonify({"error": "Missing ingredient fields."}), 400

            # Create new RecipeIngredient for each ingredient
            new_recipe_ingredient = RecipeIngredient(
                recipe_id=new_recipe.recipe_id, product_id=product_id, quantity=quantity
            )
            db.session.add(new_recipe_ingredient)

        db.session.commit()

        return jsonify({"message": "Recipe added successfully.", "recipe_id": new_recipe.recipe_id})
    except Exception as e:
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

