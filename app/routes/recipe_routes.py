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
                "description": recipe.description,
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
        description = data.get('description')
        created_by = data.get('created_by')
        ingredients = data.get('ingredients')
        product_name = data.get('productName')
        category = data.get('category')
        total_price = data.get('totalPrice')

        if not name or not description or not created_by or not ingredients:
            return jsonify({"error": "Missing required fields."}), 400

        new_recipe = Recipe(name=name, description=description, created_by=created_by)
        db.session.add(new_recipe)
        db.session.commit()

        for ingredient in ingredients:
            product_id = ingredient.get('product_id')
            quantity = ingredient.get('quantity')

            if not product_id or not quantity:
                return jsonify({"error": "Missing ingredient fields."}), 400

            new_recipe_ingredient = RecipeIngredient(
                recipe_id=new_recipe.recipe_id, product_id=product_id, quantity=quantity
            )
            db.session.add(new_recipe_ingredient)

        # Add the new product to the Product table
        new_product = Product(
            product_name=product_name,
            category=category,
            unit_price=total_price,
            supplier="The Factory",  # Default supplier
            quantity=0  # Initial quantity for the new product
        )
        db.session.add(new_product)

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
