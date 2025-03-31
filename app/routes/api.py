from flask import Blueprint, request, jsonify, session
from app.routes.auth import login_required
from app.models.food import FoodEntry, FoodReference
from app.services.food_category import FoodCategory
from app.services.food_scoring import calculate_period_score
from app import db
from config import Config, ModelType
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__)

# Create a blueprint for API routes
api_bp = Blueprint('api', __name__)

@api_bp.route('/models', methods=['GET'])
def get_models():
    """Get available models and current model"""
    return jsonify({
        'available_models': {model.value: name for model, name in Config.AVAILABLE_MODELS.items()},
        'current_model': Config.CURRENT_MODEL.value
    })

@api_bp.route('/models', methods=['POST'])
def set_model():
    """Set the current model"""
    data = request.json
    model = data.get('model')
    
    try:
        new_model = ModelType(model)
        if new_model not in Config.AVAILABLE_MODELS:
            return jsonify({'error': 'Invalid model'}), 400
            
        if new_model != ModelType.FREE and not Config.OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 400
            
        Config.CURRENT_MODEL = new_model
        return jsonify({'success': True, 'current_model': model})
    except ValueError:
        return jsonify({'error': 'Invalid model'}), 400

@api_bp.route('/food-references', methods=['GET'])
@login_required
def get_food_references():
    """Get food references from the database"""
    search = request.args.get('search', '')
    
    # Get food references (exclude not shared ones from other users)
    query = FoodReference.query.filter(
        db.or_(
            FoodReference.is_shared == True,
            FoodReference.creator_id == session['user_id']
        )
    )
    
    if search:
        query = query.filter(FoodReference.name.ilike(f"%{search}%"))
    
    # Order by:
    # 1. Most recently used first (for the user's own foods)
    # 2. User's own foods next
    # 3. Shared foods last
    # 4. Alphabetically by name within each group
    query = query.order_by(
        # User's own recently used foods first
        db.case(
            (FoodReference.creator_id == session['user_id'], 0),
            else_=1
        ),
        # Then sort by whether it's the user's own food
        db.case(
            (FoodReference.creator_id == session['user_id'], 0),
            else_=1
        ),
        # Then by name
        FoodReference.name
    )
    
    food_refs = query.all()
    
    # Transform food references to dictionary
    foods = [food.to_dict() for food in food_refs]
    
    return jsonify(foods)

@api_bp.route('/food', methods=['POST'])
@login_required
def add_food():
    """Add a new food entry"""
    data = request.json
    food_name = data.get('name', '').strip()
    brand = data.get('brand', '').strip()
    description = data.get('description', '').strip()
    meal_type = data.get('meal_type', 'snack').strip().lower()  # Default to snack if not specified
    
    # Validate meal type - only allow certain values
    allowed_meal_types = ['breakfast', 'lunch', 'dinner', 'snack', 'tea']
    if meal_type not in allowed_meal_types:
        meal_type = 'snack'  # Default to snack if invalid value
        
    # Ensure quantity is a valid number
    try:
        quantity = float(data.get('quantity', 100))
        if quantity <= 0:
            quantity = 100  # Default to 100g if invalid
    except (TypeError, ValueError):
        quantity = 100  # Default to 100g if conversion fails
    
    logger.info("\n=== Adding new food entry ===")
    logger.info(f"Food name: {food_name}, Brand: {brand}, Quantity: {quantity}g, Meal Type: {meal_type}")
    
    nutrition = None
    
    # Check if this request is coming from selecting a reference from the database
    reference_id = data.get('reference_id')
    reference = None
    
    if reference_id:
        # If a reference ID is provided, use that reference directly
        reference = FoodReference.query.get(reference_id)
    else:
        # Check if nutrition info was manually provided
        manual_nutrition = data.get('nutrition')
        if manual_nutrition:
            logger.info("Using manually provided nutrition info")
            nutrition = manual_nutrition
            
            # First check if we already have a similar reference in the database to avoid duplicates
            search_brand = brand if brand else "Generic"
            existing_reference = FoodReference.query.filter(
                FoodReference.name.ilike(f"%{food_name}%"),
                FoodReference.brand.ilike(f"%{search_brand}%"),
                db.or_(
                    FoodReference.is_shared == True,
                    FoodReference.creator_id == session['user_id']
                )
            ).first()
            
            if existing_reference:
                # Update the existing reference with new values
                logger.info("Updating existing food reference")
                reference = existing_reference
                reference.last_used_quantity = quantity
                reference.last_used_meal_type = meal_type
                reference.last_used_unit = nutrition.get('unit')
                reference.weight_per_unit = nutrition.get('weight', 100)
                # Don't update nutrition values as they might be just approximations
            else:
                # Store manual nutrition in new reference table entry
                nutri_score = FoodCategory.calculate_nutri_score(nutrition)
                food_ref = FoodReference(
                    name=food_name,
                    brand=brand,
                    calories=nutrition.get('calories', 0),
                    energy_kj=nutrition.get('energy_kj', 0),
                    protein=nutrition.get('protein', 0),
                    carbs=nutrition.get('carbs', 0),
                    sugars=nutrition.get('sugars', 0),
                    fat=nutrition.get('fat', 0),
                    saturated_fat=nutrition.get('saturated_fat', 0),
                    sodium=nutrition.get('sodium', 0),
                    fiber=nutrition.get('fiber', 0),
                    fruits_veg_nuts=nutrition.get('fruits_veg_nuts', 0),
                    nutri_score=nutri_score['grade'],
                    numeric_score=nutri_score['score'],
                    simple_score=nutri_score['simple_score'],
                    is_shared=data.get('is_shared', False),
                    creator_id=session['user_id'],
                    last_used_quantity=quantity,
                    last_used_meal_type=meal_type,
                    last_used_unit=nutrition.get('unit'),
                    weight_per_unit=nutrition.get('weight', 100)  # Store the serving weight
                )
                db.session.add(food_ref)
                db.session.commit()
                reference = food_ref
                logger.info(f"Stored manual nutrition in reference table for: {food_name}")
        else:
            # Search for an existing reference in the database
            search_brand = brand if brand else "Generic"
            reference = FoodReference.query.filter(
                FoodReference.name.ilike(f"%{food_name}%"),
                FoodReference.brand.ilike(f"%{search_brand}%"),
                db.or_(
                    FoodReference.is_shared == True,
                    FoodReference.creator_id == session['user_id']
                )
            ).first()
            
            if not reference:
                reference = FoodReference.query.filter(
                    FoodReference.name.ilike(f"%{food_name}%"),
                    db.or_(
                        FoodReference.is_shared == True,
                        FoodReference.creator_id == session['user_id']
                    )
                ).first()

            if reference:
                logger.info("Found food in reference database")
                # Use the reference brand if none specified
                if brand == 'Generic' or not brand:
                    brand = reference.brand
                
                # Update the last used quantity and meal type
                reference.last_used_quantity = quantity
                reference.last_used_meal_type = meal_type
                db.session.commit()
                logger.info(f"Updated last used quantity for {food_name}: {quantity}g, meal type: {meal_type}")
            else:
                # Get nutrition info from AI
                nutrition = FoodCategory.get_nutrition_info(food_name)
                if nutrition:
                    # Store AI nutrition in reference table
                    nutri_score = FoodCategory.calculate_nutri_score(nutrition)
                    food_ref = FoodReference(
                        name=food_name,
                        brand=brand,
                        calories=nutrition.get('calories', 0),
                        energy_kj=nutrition.get('energy_kj', 0),
                        protein=nutrition.get('protein', 0),
                        carbs=nutrition.get('carbs', 0),
                        sugars=nutrition.get('sugars', 0),
                        fat=nutrition.get('fat', 0),
                        saturated_fat=nutrition.get('saturated_fat', 0),
                        sodium=nutrition.get('sodium', 0),
                        fiber=nutrition.get('fiber', 0),
                        fruits_veg_nuts=nutrition.get('fruits_veg_nuts', 0),
                        nutri_score=nutri_score['grade'],
                        numeric_score=nutri_score['score'],
                        simple_score=nutri_score['simple_score'],
                        is_shared=data.get('is_shared', False),
                        creator_id=session['user_id'],
                        last_used_quantity=quantity,
                        last_used_meal_type=meal_type,
                        last_used_unit=nutrition.get('unit'),
                        weight_per_unit=nutrition.get('weight', 100)  # Store the serving weight
                    )
                    db.session.add(food_ref)
                    db.session.commit()
                    reference = food_ref
                    logger.info(f"Stored AI nutrition in reference table for: {food_name}")
    
    # If we have a reference, extract nutrition from it
    if reference:
        nutrition = {
            'calories': reference.calories,
            'energy_kj': reference.energy_kj,
            'protein': reference.protein,
            'carbs': reference.carbs,
            'sugars': reference.sugars,
            'fat': reference.fat,
            'saturated_fat': reference.saturated_fat,
            'sodium': reference.sodium,
            'fiber': reference.fiber,
            'fruits_veg_nuts': reference.fruits_veg_nuts
        }
        nutri_score = {
            'grade': reference.nutri_score,
            'score': reference.numeric_score,
            'simple_score': reference.simple_score
        }
    
    if nutrition:
        if 'nutri_score' not in locals():
            nutri_score = FoodCategory.calculate_nutri_score(nutrition)
        
        # Create new food entry
        entry = FoodEntry(
            name=food_name,
            brand=brand,
            description=description,
            quantity=quantity,
            meal_type=meal_type,
            user_id=session['user_id'],
            calories=nutrition.get('calories', 0),
            energy_kj=nutrition.get('energy_kj', 0),
            protein=nutrition.get('protein', 0),
            carbs=nutrition.get('carbs', 0),
            sugars=nutrition.get('sugars', 0),
            fat=nutrition.get('fat', 0),
            saturated_fat=nutrition.get('saturated_fat', 0),
            sodium=nutrition.get('sodium', 0),
            fiber=nutrition.get('fiber', 0),
            fruits_veg_nuts=nutrition.get('fruits_veg_nuts', 0),
            nutri_score=nutri_score['grade'],
            numeric_score=nutri_score['score'],
            simple_score=nutri_score['simple_score']
        )
        
        db.session.add(entry)
        db.session.commit()
        logger.info(f"Added new food entry for: {food_name}")
        
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to get nutrition information'}), 400

@api_bp.route('/food/<int:id>', methods=['DELETE'])
@login_required
def delete_food(id):
    entry = FoodEntry.query.get_or_404(id)
    
    # Check if the entry belongs to the current user
    if entry.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/daily-score')
@login_required
def get_daily_score():
    today = datetime.now().date()
    entries = FoodEntry.query.filter(
        FoodEntry.date == today,
        FoodEntry.user_id == session['user_id']  # Filter by user
    ).all()
    return calculate_period_score(entries)

@api_bp.route('/weekly-score')
@login_required
def get_weekly_score():
    end_date = datetime.now().date()
    # Calculate the Monday of the current week
    start_date = end_date - timedelta(days=end_date.weekday())  # weekday() returns 0 for Monday
    
    entries = FoodEntry.query.filter(
        FoodEntry.date.between(start_date, end_date),
        FoodEntry.user_id == session['user_id']
    ).order_by(FoodEntry.date.desc()).all()
    
    # If all entries are from today, return today's score
    if all(entry.date == end_date for entry in entries):
        return calculate_period_score(entries)
    
    # Group entries by date
    entries_by_date = {}
    for entry in entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str not in entries_by_date:
            entries_by_date[date_str] = []
        entries_by_date[date_str].append(entry)
    
    # Calculate daily scores and average them
    daily_scores = []
    total_nutrition = {
        'calories': 0,
        'energy_kj': 0,
        'protein': 0,
        'carbs': 0,
        'sugars': 0,
        'fat': 0,
        'saturated_fat': 0,
        'sodium': 0,
        'fiber': 0,
        'fruits_veg_nuts': 0
    }
    
    for date, day_entries in entries_by_date.items():
        daily_score = calculate_period_score(day_entries)
        daily_data = daily_score.get_json()
        daily_scores.append({
            'date': date,
            'score': daily_data['score'],
            'simple_score': daily_data['simple_score'],
            'grade': daily_data['grade'],
            'nutrition': daily_data['daily_nutrition']
        })
        
        # Add to total nutrition
        for key in total_nutrition:
            total_nutrition[key] += daily_data['daily_nutrition'][key]
    
    # Calculate averages
    num_days = len(entries_by_date)
    if num_days > 0:
        for key in total_nutrition:
            if key == 'fruits_veg_nuts':
                # For percentages, use arithmetic mean
                total_nutrition[key] = round(total_nutrition[key] / num_days, 1)
            else:
                # For absolute values, divide by number of days
                total_nutrition[key] = round(total_nutrition[key] / num_days, 1)
        
        # Calculate overall score based on average nutrition
        nutri_score = FoodCategory.calculate_nutri_score(total_nutrition)
        
        return jsonify({
            'score': nutri_score['score'],
            'simple_score': nutri_score['simple_score'],
            'grade': nutri_score['grade'],
            'daily_scores': daily_scores,
            'daily_nutrition': total_nutrition,
            'num_days': num_days
        })
    else:
        return jsonify({
            'score': 0,
            'simple_score': 50,
            'grade': 'C',
            'daily_scores': [],
            'daily_nutrition': total_nutrition,
            'num_days': 0
        })

@api_bp.route('/monthly-score')
@login_required
def get_monthly_score():
    today = datetime.now().date()
    # Calculate the first day of the current month
    start_date = today.replace(day=1)
    # Calculate the last day of the current month
    if today.month == 12:
        end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    entries = FoodEntry.query.filter(
        FoodEntry.date.between(start_date, end_date),
        FoodEntry.user_id == session['user_id']
    ).order_by(FoodEntry.date.desc()).all()
    
    # If all entries are from today, return today's score
    if all(entry.date == today for entry in entries):
        return calculate_period_score(entries)
    
    # Group entries by date
    entries_by_date = {}
    for entry in entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str not in entries_by_date:
            entries_by_date[date_str] = []
        entries_by_date[date_str].append(entry)
    
    # Calculate daily scores and average them
    daily_scores = []
    total_nutrition = {
        'calories': 0,
        'energy_kj': 0,
        'protein': 0,
        'carbs': 0,
        'sugars': 0,
        'fat': 0,
        'saturated_fat': 0,
        'sodium': 0,
        'fiber': 0,
        'fruits_veg_nuts': 0
    }
    
    for date, day_entries in entries_by_date.items():
        daily_score = calculate_period_score(day_entries)
        daily_data = daily_score.get_json()
        daily_scores.append({
            'date': date,
            'score': daily_data['score'],
            'simple_score': daily_data['simple_score'],
            'grade': daily_data['grade'],
            'nutrition': daily_data['daily_nutrition']
        })
        
        # Add to total nutrition
        for key in total_nutrition:
            total_nutrition[key] += daily_data['daily_nutrition'][key]
    
    # Calculate averages
    num_days = len(entries_by_date)
    if num_days > 0:
        for key in total_nutrition:
            if key == 'fruits_veg_nuts':
                # For percentages, use arithmetic mean
                total_nutrition[key] = round(total_nutrition[key] / num_days, 1)
            else:
                # For absolute values, divide by number of days
                total_nutrition[key] = round(total_nutrition[key] / num_days, 1)
        
        # Calculate overall score based on average nutrition
        nutri_score = FoodCategory.calculate_nutri_score(total_nutrition)
        
        return jsonify({
            'score': nutri_score['score'],
            'simple_score': nutri_score['simple_score'],
            'grade': nutri_score['grade'],
            'daily_scores': daily_scores,
            'daily_nutrition': total_nutrition,
            'num_days': num_days
        })
    else:
        return jsonify({
            'score': 0,
            'simple_score': 50,
            'grade': 'C',
            'daily_scores': [],
            'daily_nutrition': total_nutrition,
            'num_days': 0
        })

@api_bp.route('/food-references/<int:id>', methods=['DELETE'])
@login_required
def delete_food_reference(id):
    """Delete a food reference"""
    food_ref = FoodReference.query.get_or_404(id)
    
    # Only allow deletion if you created the food
    if food_ref.creator_id != session['user_id']:
        return jsonify({'error': 'Unauthorized - you can only delete foods you created'}), 403
    
    # Delete the food reference
    db.session.delete(food_ref)
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/serving-sizes/<food_name>')
def get_serving_sizes(food_name):
    """Get appropriate serving sizes for a food item"""
    serving_sizes = Config.get_serving_sizes(food_name)
    return jsonify(serving_sizes)

@api_bp.route('/food-type/<food_name>')
def get_food_type_info(food_name):
    """Get food type information using LLM"""
    try:
        # First check if this food exists in our database and has been used before
        food_ref = FoodReference.query.filter(
            FoodReference.name.ilike(f"%{food_name}%"),
            db.or_(
                FoodReference.is_shared == True,
                FoodReference.creator_id == session.get('user_id')
            )
        ).first()
        
        # If we have a record with last used data, prefer that
        if food_ref and food_ref.last_used_quantity:
            food_type = Config.get_food_type(food_name)
            serving_sizes = Config.SERVING_SIZES.get(food_type, Config.SERVING_SIZES['default'])
            
            # Prepare a custom options list with the last used quantity as the first option
            custom_options = [{'label': f"Last used: {food_ref.last_used_quantity}g", 'value': food_ref.last_used_quantity}]
            custom_options.extend(serving_sizes['sizes'])
            
            # Create the response
            response = {
                'food_type': food_type,
                'unit': food_ref.last_used_unit or serving_sizes['unit'],
                'last_used_quantity': food_ref.last_used_quantity,
                'last_used_meal_type': food_ref.last_used_meal_type or 'snack',
                'serving_sizes': {
                    'unit': serving_sizes['unit'],
                    'sizes': custom_options
                },
                'default_quantity': food_ref.last_used_quantity,
                'weight_per_unit': None
            }
            
            return jsonify(response)
        
        # If no record or no last used data, use the LLM to get food type info
        if Config.CURRENT_MODEL == ModelType.FREE:
            prompt = Config.HUGGINGFACE_FOOD_TYPE_PROMPT.format(food_name=food_name)
            headers = {"Authorization": f"Bearer {Config.HUGGINGFACE_API_KEY}"}
            api_url = f"{Config.HUGGINGFACE_API_BASE_URL}/models/google/flan-t5-base"
            
            response = requests.post(api_url, headers=headers, json={
                "inputs": prompt,
                "parameters": {"max_length": 50}
            })
            
            if response.status_code == 200:
                result = response.json()[0]["generated_text"].strip().lower()
                if '|' in result:
                    parts = result.split('|')
                    if len(parts) == 3:
                        food_type, unit, weight = parts
                        weight = float(weight)
                    else:
                        food_type = parts[0]
                        unit = parts[1] if len(parts) > 1 else 'g'
                        weight = None
                else:
                    food_type = result
                    unit = 'g'
                    weight = None
            else:
                food_type = Config.get_food_type(food_name)
                unit = 'g'
                weight = None
        else:
            if Config.OPENAI_API_KEY:
                import openai
                
                messages = [
                    {"role": "system", "content": Config.OPENAI_FOOD_TYPE_SYSTEM_PROMPT},
                    {"role": "user", "content": Config.OPENAI_FOOD_TYPE_PROMPT.format(food_name=food_name)}
                ]
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=50
                )
                
                if response.choices:
                    result = response.choices[0].message.content.strip().lower()
                    if '|' in result:
                        parts = result.split('|')
                        if len(parts) == 3:
                            food_type, unit, weight = parts
                            weight = float(weight)
                        else:
                            food_type = parts[0]
                            unit = parts[1] if len(parts) > 1 else 'g'
                            weight = None
                    else:
                        food_type = result
                        unit = 'g'
                        weight = None
                else:
                    food_type = Config.get_food_type(food_name)
                    unit = 'g'
                    weight = None
            else:
                food_type = Config.get_food_type(food_name)
                unit = 'g'
                weight = None
        
        # If we didn't get a weight from the model, try to get it from our standard weights
        if weight is None and unit in ['cookie', 'unit', 'piece', 'slice', 'tablespoon', 'cup']:
            food_name_lower = food_name.lower()
            
            if unit == 'cookie':
                if 'oreo' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['cookie']['oreo']
                elif 'chocolate chip' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['cookie']['chocolate_chip']
                else:
                    weight = Config.STANDARD_WEIGHTS['cookie']['standard']
            
            elif unit == 'unit' and 'cracker' in food_name_lower:
                if 'saltine' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['cracker']['saltine']
                elif 'graham' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['cracker']['graham']
                else:
                    weight = Config.STANDARD_WEIGHTS['cracker']['standard']
            
            elif unit == 'piece' and food_type == 'fruits':
                if 'apple' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['fruit']['apple']
                elif 'banana' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['fruit']['banana']
                elif 'orange' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['fruit']['orange']
                else:
                    weight = Config.STANDARD_WEIGHTS['fruit']['standard']
            
            elif unit == 'slice' and 'bread' in food_name_lower:
                if 'white' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['bread']['white']
                elif 'whole wheat' in food_name_lower or 'wholemeal' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['bread']['whole_wheat']
                else:
                    weight = Config.STANDARD_WEIGHTS['bread']['standard']
            
            elif unit == 'tablespoon':
                weight = Config.STANDARD_WEIGHTS['tablespoon']
            
            elif unit == 'cup':
                if food_type == 'beverages':
                    weight = Config.STANDARD_WEIGHTS['cup']['liquid']
                elif 'cereal' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['cup']['cereal']
                elif 'leafy' in food_name_lower or 'salad' in food_name_lower:
                    weight = Config.STANDARD_WEIGHTS['cup']['leafy_greens']
                else:
                    weight = Config.STANDARD_WEIGHTS['cup']['liquid']
        
        # Get serving sizes based on the unit and weight
        if unit in ['cookie', 'unit', 'piece', 'slice']:
            serving_sizes = {
                'unit': unit,
                'sizes': [
                    {'label': f'1 {unit}', 'value': weight},
                    {'label': f'2 {unit}s', 'value': weight * 2},
                    {'label': f'3 {unit}s', 'value': weight * 3},
                    {'label': f'Custom amount ({unit}s)', 'value': 'custom'}
                ]
            }
        elif unit == 'tablespoon':
            serving_sizes = {
                'unit': unit,
                'sizes': [
                    {'label': '1 tablespoon', 'value': weight},
                    {'label': '2 tablespoons', 'value': weight * 2},
                    {'label': '3 tablespoons', 'value': weight * 3},
                    {'label': 'Custom amount (tbsp)', 'value': 'custom'}
                ]
            }
        elif unit == 'cup' and food_type == 'beverages':
            serving_sizes = {
                'unit': 'ml',
                'sizes': [
                    {'label': 'Small glass (200ml)', 'value': 200},
                    {'label': 'Regular glass (250ml)', 'value': 250},
                    {'label': 'Large glass (330ml)', 'value': 330},
                    {'label': 'Custom volume (ml)', 'value': 'custom'}
                ]
            }
        else:
            serving_sizes = Config.SERVING_SIZES.get(food_type, Config.SERVING_SIZES['default'])
        
        # Get default quantity based on food type and unit
        default_quantity = serving_sizes['sizes'][1]['value'] if len(serving_sizes['sizes']) > 1 else weight or 100
        
        # For display purposes, convert unit 'unit' to a more natural name
        display_unit = unit
        if unit == 'unit':
            display_unit = 'piece'
        
        return jsonify({
            'food_type': food_type,
            'serving_sizes': serving_sizes,
            'default_quantity': default_quantity,
            'unit': unit,
            'display_unit': display_unit,
            'weight_per_unit': weight
        })
        
    except Exception as e:
        logger.error(f"Error getting food type info: {str(e)}")
        # Fallback to basic detection
        food_type = Config.get_food_type(food_name)
        serving_sizes = Config.SERVING_SIZES.get(food_type, Config.SERVING_SIZES['default'])
        return jsonify({
            'food_type': food_type,
            'serving_sizes': serving_sizes,
            'default_quantity': 100,
            'unit': 'g',
            'display_unit': 'g',
            'weight_per_unit': None
        })

@api_bp.route('/food-info/verify', methods=['POST'])
@login_required
def verify_food_info():
    """First step: Verify food information"""
    data = request.json
    food_name = data.get('name', '').strip()
    brand = data.get('brand', '').strip()
    description = data.get('description', '').strip()
    
    if not food_name:
        return jsonify({'error': 'Food name is required'}), 400
    
    # Prepare a formatted description including optional brand and description
    formatted_description = food_name
    if brand:
        formatted_description += f" ({brand})"
    if description:
        formatted_description += f" - {description}"
    
    # Check if we already have this food in our database
    reference = None
    search_brand = brand if brand else "Generic"
    
    # Try to find exact match with name and brand
    reference = FoodReference.query.filter(
        FoodReference.name.ilike(f"%{food_name}%"),
        FoodReference.brand.ilike(f"%{search_brand}%"),
        db.or_(
            FoodReference.is_shared == True,
            FoodReference.creator_id == session['user_id']
        )
    ).first()
    
    if not reference:
        # If not found with the specific brand, try with just the name
        reference = FoodReference.query.filter(
            FoodReference.name.ilike(f"%{food_name}%"),
            db.or_(
                FoodReference.is_shared == True,
                FoodReference.creator_id == session['user_id']
            )
        ).first()
    
    return jsonify({
        'verified': True,
        'food_name': food_name,
        'brand': brand,
        'description': description,
        'formatted_description': formatted_description,
        'found_in_db': reference is not None,
        'reference': reference.to_dict() if reference else None
    })

@api_bp.route('/food-info/serving-size', methods=['POST'])
@login_required
def get_recommended_serving_size():
    """Second step: Get recommended serving size for the food"""
    data = request.json
    food_name = data.get('name', '').strip()
    brand = data.get('brand', '').strip()
    description = data.get('description', '').strip()
    
    if not food_name:
        return jsonify({'error': 'Food name is required'}), 400
    
    # Check if we have this food in our database first
    search_brand = brand if brand else "Generic"
    reference = FoodReference.query.filter(
        FoodReference.name.ilike(f"%{food_name}%"),
        FoodReference.brand.ilike(f"%{search_brand}%"),
        db.or_(
            FoodReference.is_shared == True,
            FoodReference.creator_id == session['user_id']
        )
    ).first()
    
    if not reference:
        # Try with just the name
        reference = FoodReference.query.filter(
            FoodReference.name.ilike(f"%{food_name}%"),
            db.or_(
                FoodReference.is_shared == True,
                FoodReference.creator_id == session['user_id']
            )
        ).first()
    
    # If found in database, use the last used quantity, unit, and weight
    if reference and reference.last_used_quantity:
        logger.info(f"Using serving size from database for {food_name}")
        
        # Get the exact values from the database record
        exact_quantity = float(reference.last_used_quantity)
        unit = reference.last_used_unit
        weight_per_unit = float(reference.weight_per_unit) if reference.weight_per_unit else exact_quantity
        
        # Determine display options based on unit type
        if unit in ['cookie', 'piece', 'slice', 'unit', 'egg', 'cup', 'tbsp', 'tsp']:
            # Format with pieces
            pieces = 1 if weight_per_unit == exact_quantity else exact_quantity / weight_per_unit if weight_per_unit > 0 else 1
            
            serving_size = {
                'food_type': 'from_database',
                'unit': unit,
                'weight': weight_per_unit,  # Exact weight per unit
                'default_serving': {
                    'quantity': exact_quantity,  # Use exact quantity from DB
                    'unit': unit,
                    'description': f"{pieces} {unit}{'' if pieces == 1 else 's'} ({exact_quantity}g)"
                },
                'options': [
                    {'label': f"{pieces} {unit}{'' if pieces == 1 else 's'} ({exact_quantity}g)", 'value': exact_quantity},
                    {'label': f"{pieces*2} {unit}s ({exact_quantity*2}g)", 'value': exact_quantity*2},
                    {'label': f"1 {unit} ({weight_per_unit}g)", 'value': weight_per_unit},
                    {'label': 'Custom amount (g)', 'value': 'custom'}
                ],
                'last_used_meal_type': reference.last_used_meal_type  # Include last used meal type
            }
            return jsonify(serving_size)
        else:
            # Default options for weight/volume
            serving_size = {
                'food_type': 'from_database',
                'unit': 'g',
                'weight': 100,
                'default_serving': {
                    'quantity': exact_quantity,  # Use exact quantity from DB
                    'unit': 'g',
                    'description': f"{exact_quantity}g"
                },
                'options': [
                    {'label': f"{exact_quantity}g", 'value': exact_quantity},
                    {'label': f"100g", 'value': 100},
                    {'label': f"150g", 'value': 150},
                    {'label': f"200g", 'value': 200},
                    {'label': 'Custom amount (g)', 'value': 'custom'}
                ],
                'last_used_meal_type': reference.last_used_meal_type  # Include last used meal type
            }
            return jsonify(serving_size)
    
    # Prepare a full description for better LLM context
    full_description = food_name
    if brand:
        full_description += f" made by {brand}"
    if description:
        full_description += f" ({description})"
    
    try:
        # Use the LLM to get food type information
        if Config.CURRENT_MODEL == ModelType.FREE:
            prompt = Config.HUGGINGFACE_FOOD_TYPE_PROMPT.format(food_name=full_description)
            headers = {"Authorization": f"Bearer {Config.HUGGINGFACE_API_KEY}"}
            api_url = f"{Config.HUGGINGFACE_API_BASE_URL}/models/google/flan-t5-base"
            
            response = requests.post(api_url, headers=headers, json={
                "inputs": prompt,
                "parameters": {
                    "max_length": 50,
                    "temperature": 0.2,
                    "num_return_sequences": 1,
                    "do_sample": True
                }
            })
            
            if response.status_code == 200:
                result = response.json()[0]["generated_text"].strip().lower()
                logger.info(f"Hugging Face serving size response: {result}")
                
                # Parse the response
                if '|' in result:
                    parts = result.split('|')
                    if len(parts) >= 4:  # Now expecting 4 parts with the quantity
                        food_type, unit, weight, suggested_qty = parts[0], parts[1], float(parts[2]), int(float(parts[3]))
                        
                        # Set proper display options based on unit type
                        if unit in ['cookie', 'piece', 'slice', 'unit', 'egg']:
                            # Use the suggested quantity from the LLM response
                            total_weight = weight * suggested_qty
                            
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'suggested_quantity': suggested_qty,
                                'default_serving': {
                                    'quantity': total_weight,
                                    'unit': unit,
                                    'description': f"{suggested_qty} {unit}{'' if suggested_qty == 1 else 's'} ({total_weight}g)"
                                },
                                'options': [
                                    {'label': f"{suggested_qty} {unit}{'' if suggested_qty == 1 else 's'} ({total_weight}g)", 'value': total_weight},
                                    {'label': f"{suggested_qty*2} {unit}s ({total_weight*2}g)", 'value': total_weight*2},
                                    {'label': f"1 {unit} ({weight}g)", 'value': weight},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        else:
                            # Default options for weight/volume
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'default_serving': {
                                    'quantity': weight,
                                    'unit': unit,
                                    'description': f"{weight}g"
                                },
                                'options': [
                                    {'label': f"100g", 'value': 100},
                                    {'label': f"150g", 'value': 150},
                                    {'label': f"200g", 'value': 200},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        return jsonify(serving_size)
                    elif len(parts) >= 3:  # Backward compatibility for old format
                        food_type, unit, weight = parts[0], parts[1], float(parts[2])
                        
                        # Set proper display options based on unit type
                        if unit in ['cookie', 'piece', 'slice', 'unit', 'egg']:
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'default_serving': {
                                    'quantity': weight,
                                    'unit': unit,
                                    'description': f"1 {unit} ({weight}g)"
                                },
                                'options': [
                                    {'label': f"1 {unit} ({weight}g)", 'value': weight},
                                    {'label': f"2 {unit}s ({weight*2}g)", 'value': weight*2},
                                    {'label': f"3 {unit}s ({weight*3}g)", 'value': weight*3},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        else:
                            # Default options for weight/volume
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'default_serving': {
                                    'quantity': weight,
                                    'unit': unit,
                                    'description': f"{weight}g"
                                },
                                'options': [
                                    {'label': f"100g", 'value': 100},
                                    {'label': f"150g", 'value': 150},
                                    {'label': f"200g", 'value': 200},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        return jsonify(serving_size)
        else:
            import openai
            
            messages = [
                {"role": "system", "content": Config.OPENAI_FOOD_TYPE_SYSTEM_PROMPT},
                {"role": "user", "content": Config.OPENAI_FOOD_TYPE_PROMPT.format(food_name=full_description)}
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=50
            )
            
            if response.choices:
                result = response.choices[0].message.content.strip().lower()
                logger.info(f"OpenAI serving size response: {result}")
                
                # Parse the response
                if '|' in result:
                    parts = result.split('|')
                    if len(parts) >= 4:  # Now expecting 4 parts with the quantity
                        food_type, unit, weight, suggested_qty = parts[0], parts[1], float(parts[2]), int(float(parts[3]))
                        
                        # Set proper display options based on unit type
                        if unit in ['cookie', 'piece', 'slice', 'unit', 'egg']:
                            # Use the suggested quantity from the LLM response
                            total_weight = weight * suggested_qty
                            
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'suggested_quantity': suggested_qty,
                                'default_serving': {
                                    'quantity': total_weight,
                                    'unit': unit,
                                    'description': f"{suggested_qty} {unit}{'' if suggested_qty == 1 else 's'} ({total_weight}g)"
                                },
                                'options': [
                                    {'label': f"{suggested_qty} {unit}{'' if suggested_qty == 1 else 's'} ({total_weight}g)", 'value': total_weight},
                                    {'label': f"{suggested_qty*2} {unit}s ({total_weight*2}g)", 'value': total_weight*2},
                                    {'label': f"1 {unit} ({weight}g)", 'value': weight},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        else:
                            # Default options for weight/volume
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'default_serving': {
                                    'quantity': weight,
                                    'unit': unit,
                                    'description': f"{weight}g"
                                },
                                'options': [
                                    {'label': f"100g", 'value': 100},
                                    {'label': f"150g", 'value': 150},
                                    {'label': f"200g", 'value': 200},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        return jsonify(serving_size)
                    elif len(parts) >= 3:  # Backward compatibility for old format
                        food_type, unit, weight = parts[0], parts[1], float(parts[2])
                        
                        # Set proper display options based on unit type
                        if unit in ['cookie', 'piece', 'slice', 'unit', 'egg']:
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'default_serving': {
                                    'quantity': weight,
                                    'unit': unit,
                                    'description': f"1 {unit} ({weight}g)"
                                },
                                'options': [
                                    {'label': f"1 {unit} ({weight}g)", 'value': weight},
                                    {'label': f"2 {unit}s ({weight*2}g)", 'value': weight*2},
                                    {'label': f"3 {unit}s ({weight*3}g)", 'value': weight*3},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        else:
                            # Default options for weight/volume
                            serving_size = {
                                'food_type': food_type,
                                'unit': unit,
                                'weight': weight,
                                'default_serving': {
                                    'quantity': weight,
                                    'unit': unit,
                                    'description': f"{weight}g"
                                },
                                'options': [
                                    {'label': f"100g", 'value': 100},
                                    {'label': f"150g", 'value': 150},
                                    {'label': f"200g", 'value': 200},
                                    {'label': 'Custom amount (g)', 'value': 'custom'}
                                ]
                            }
                        return jsonify(serving_size)
        
        # If we reach here, either the API call failed or parsing failed
        # Return default serving sizes
        logger.info(f"Using default serving sizes for {food_name}")
        default_serving = {
            'food_type': 'default',
            'unit': 'g',
            'weight': 100,
            'default_serving': {
                'quantity': 100,
                'unit': 'g',
                'description': '100g'
            },
            'options': [
                {'label': '100g', 'value': 100},
                {'label': '150g', 'value': 150},
                {'label': '200g', 'value': 200},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        }
        return jsonify(default_serving)
        
    except Exception as e:
        logger.error(f"Error getting serving size info: {str(e)}")
        # Return default serving sizes
        default_serving = {
            'food_type': 'default',
            'unit': 'g',
            'weight': 100,
            'default_serving': {
                'quantity': 100,
                'unit': 'g',
                'description': '100g'
            },
            'options': [
                {'label': '100g', 'value': 100},
                {'label': '150g', 'value': 150},
                {'label': '200g', 'value': 200},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        }
        return jsonify(default_serving)

@api_bp.route('/food-info/nutrition', methods=['POST'])
@login_required
def get_nutrition_information():
    """Third step: Get nutrition information for the food"""
    data = request.json
    food_name = data.get('name', '').strip()
    brand = data.get('brand', '').strip()
    description = data.get('description', '').strip()
    quantity = data.get('quantity', 100)
    
    # Check if manual nutrition data was provided
    manual_nutrition = data.get('nutrition')
    
    # Ensure quantity is a valid number
    try:
        quantity = float(quantity)
        if quantity <= 0:
            quantity = 100  # Default to 100g if invalid
    except (TypeError, ValueError):
        quantity = 100  # Default to 100g if conversion fails
    
    if not food_name:
        return jsonify({'error': 'Food name is required'}), 400
    
    # Prepare a full description for better LLM context
    full_description = food_name
    if brand:
        full_description += f" made by {brand}"
    if description:
        full_description += f" ({description})"
    
    # If we have manual nutrition data, use that
    if manual_nutrition:
        logger.info(f"Using manually provided nutrition for {food_name}")
        
        # Get the custom serving unit and weight if provided
        serving_unit = manual_nutrition.get('unit')
        serving_weight = manual_nutrition.get('weight', 100)
        
        # When manually entering nutrition data, users expect to enter the values for the EXACT serving,
        # not per 100g. We need to convert these to per 100g for storage
        nutrition_per_serving = manual_nutrition
        
        # Calculate the factor to convert to per 100g (for storage in DB)
        conversion_factor = 100.0 / quantity
        
        # Convert nutrition to per 100g values for storage
        nutrition_per_100g = {
            'calories': round(nutrition_per_serving.get('calories', 0) * conversion_factor, 1),
            'energy_kj': round(nutrition_per_serving.get('energy_kj', 0) * conversion_factor, 1),
            'protein': round(nutrition_per_serving.get('protein', 0) * conversion_factor, 1),
            'carbs': round(nutrition_per_serving.get('carbs', 0) * conversion_factor, 1),
            'sugars': round(nutrition_per_serving.get('sugars', 0) * conversion_factor, 1),
            'fat': round(nutrition_per_serving.get('fat', 0) * conversion_factor, 1),
            'saturated_fat': round(nutrition_per_serving.get('saturated_fat', 0) * conversion_factor, 1),
            'sodium': round(nutrition_per_serving.get('sodium', 0) * conversion_factor, 1),
            'fiber': round(nutrition_per_serving.get('fiber', 0) * conversion_factor, 1),
            'fruits_veg_nuts': nutrition_per_serving.get('fruits_veg_nuts', 0)  # Percentage stays the same
        }
        
        # Calculate Nutri-Score using the per 100g values
        nutri_score = FoodCategory.calculate_nutri_score(nutrition_per_100g)
        
        # No need to adjust for quantity again, since the original values are already for the specified quantity
        adjusted_nutrition = nutrition_per_serving
        
        # Return the original per-serving values as nutrition, and also include the per 100g values
        return jsonify({
            'nutrition': nutrition_per_100g,  # Per 100g for storage
            'adjusted_nutrition': adjusted_nutrition,  # The actual values entered by user
            'per_serving': nutrition_per_serving,  # Add the per_serving values explicitly
            'nutri_score': nutri_score,
            'source': 'manual',
            'from_reference': False,
            'unit': serving_unit,
            'weight': serving_weight,
            'is_manual': True  # Flag to indicate these are manually entered values
        })
    
    # Check if we have this food in our reference database
    reference = None
    search_brand = brand if brand else "Generic"
    
    # Try to find exact match with name and brand
    reference = FoodReference.query.filter(
        FoodReference.name.ilike(f"%{food_name}%"),
        FoodReference.brand.ilike(f"%{search_brand}%"),
        db.or_(
            FoodReference.is_shared == True,
            FoodReference.creator_id == session['user_id']
        )
    ).first()
    
    if not reference:
        # If not found with the specific brand, try with just the name
        reference = FoodReference.query.filter(
            FoodReference.name.ilike(f"%{food_name}%"),
            db.or_(
                FoodReference.is_shared == True,
                FoodReference.creator_id == session['user_id']
            )
        ).first()
    
    if reference:
        logger.info(f"Found existing nutrition info for {food_name}")
        # Use existing reference
        nutrition = {
            'calories': reference.calories,
            'energy_kj': reference.energy_kj,
            'protein': reference.protein,
            'carbs': reference.carbs,
            'sugars': reference.sugars,
            'fat': reference.fat,
            'saturated_fat': reference.saturated_fat,
            'sodium': reference.sodium,
            'fiber': reference.fiber,
            'fruits_veg_nuts': reference.fruits_veg_nuts
        }
        
        # Include the serving unit if available
        serving_unit = reference.last_used_unit
        serving_weight = reference.weight_per_unit
        
        # If we have a serving weight that's the same as the quantity, use it directly
        if serving_weight and abs(serving_weight - quantity) < 0.01:
            # This is likely a 1-piece serving where we should preserve the exact values
            serving_weight = quantity  # Match it exactly to avoid decimal display issues

        # Calculate Nutri-Score
        nutri_score = FoodCategory.calculate_nutri_score(nutrition)
        
        # Adjust values for the specified quantity
        factor = quantity / 100.0
        adjusted_nutrition = {k: round(v * factor, 1) for k, v in nutrition.items()}
        adjusted_nutrition['fruits_veg_nuts'] = nutrition['fruits_veg_nuts']  # Percentage stays the same
        
        return jsonify({
            'nutrition': nutrition,  # Per 100g
            'adjusted_nutrition': adjusted_nutrition,  # Adjusted for quantity
            'nutri_score': nutri_score,
            'source': 'database',
            'from_reference': True,
            'reference_id': reference.id,
            'unit': serving_unit,
            'weight': serving_weight
        })
    else:
        # Use AI to get nutrition information
        logger.info(f"Getting nutrition info from AI for {full_description}")
        nutrition = FoodCategory.get_nutrition_info(full_description)
        
        if nutrition:
            # Get Nutri-Score from nutrition data
            nutri_score = nutrition.get('nutri_score', FoodCategory.calculate_nutri_score(nutrition))
            
            # Adjust values for the specified quantity
            factor = quantity / 100.0
            adjusted_nutrition = {k: round(v * factor, 1) for k, v in nutrition.items() if k != 'nutri_score'}
            adjusted_nutrition['fruits_veg_nuts'] = nutrition['fruits_veg_nuts']  # Percentage stays the same
            
            return jsonify({
                'nutrition': nutrition,  # Per 100g
                'adjusted_nutrition': adjusted_nutrition,  # Adjusted for quantity
                'nutri_score': nutri_score,
                'source': 'ai',
                'from_reference': False
            })
        else:
            return jsonify({'error': 'Failed to get nutrition information'}), 400 