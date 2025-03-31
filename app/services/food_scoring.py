from flask import jsonify
from app.services.food_category import FoodCategory
import logging

logger = logging.getLogger(__name__)

def calculate_period_score(entries):
    """Calculate nutrition score for a period (day/week/month) based on food entries."""
    if not entries:
        return jsonify({
            'score': 0,
            'simple_score': 50,
            'grade': 'C',
            'entries': [],
            'daily_nutrition': {
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
        })
    
    # If there's only one entry, return its score directly
    if len(entries) == 1:
        entry = entries[0]
        nutrition = entry.get_adjusted_nutrition()
        return jsonify({
            'score': entry.numeric_score,
            'simple_score': entry.simple_score,
            'grade': entry.nutri_score,
            'entries': [{
                'id': entry.id,
                'name': entry.name,
                'brand': entry.brand or '',
                'description': entry.description or '',
                'meal_type': entry.meal_type,
                'quantity': entry.quantity,
                'nutrition': nutrition,
                'date': entry.date.strftime('%Y-%m-%d')
            }],
            'daily_nutrition': {
                'calories': nutrition['calories'],
                'energy_kj': nutrition['energy_kj'],
                'protein': nutrition['protein'],
                'carbs': nutrition['carbs'],
                'sugars': nutrition['sugars'],
                'fat': nutrition['fat'],
                'saturated_fat': nutrition['saturated_fat'],
                'sodium': nutrition['sodium'],
                'fiber': nutrition['fiber'],
                'fruits_veg_nuts': nutrition['fruits_veg_nuts']
            }
        })
    
    # For multiple entries, calculate weighted average
    daily_nutrition = {
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
    
    total_calories = 0
    entries_data = []
    
    # First pass: calculate total calories and collect entries data
    for entry in entries:
        nutrition = entry.get_adjusted_nutrition()
        total_calories += nutrition['calories']
        entries_data.append({
            'id': entry.id,
            'name': entry.name,
            'brand': entry.brand or '',
            'description': entry.description or '',
            'meal_type': entry.meal_type,
            'quantity': entry.quantity,
            'nutrition': nutrition,
            'date': entry.date.strftime('%Y-%m-%d')
        })
    
    # Second pass: calculate weighted averages based on caloric contribution
    for entry in entries:
        nutrition = entry.get_adjusted_nutrition()
        weight = nutrition['calories'] / total_calories if total_calories > 0 else 1.0 / len(entries)
        
        for key in daily_nutrition:
            if key == 'fruits_veg_nuts':
                # For fruits/veg/nuts, use weighted average
                daily_nutrition[key] += nutrition[key] * weight
            else:
                # For other nutrients, sum the absolute values
                daily_nutrition[key] += nutrition[key]
    
    # Round final totals
    for key in daily_nutrition:
        daily_nutrition[key] = round(daily_nutrition[key], 1)
    
    # Calculate Nutri-Score based on total nutrition
    nutri_score = FoodCategory.calculate_nutri_score(daily_nutrition)
    
    return jsonify({
        'score': nutri_score['score'],
        'simple_score': nutri_score['simple_score'],
        'grade': nutri_score['grade'],
        'entries': entries_data,
        'daily_nutrition': daily_nutrition
    }) 