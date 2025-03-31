from app import db
from datetime import datetime
import sqlalchemy as sa

class FoodReference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False, default='Generic')
    calories = db.Column(db.Float, nullable=False)
    energy_kj = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    sugars = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    saturated_fat = db.Column(db.Float, nullable=False)
    sodium = db.Column(db.Float, nullable=False)  # in mg
    fiber = db.Column(db.Float, nullable=False)
    fruits_veg_nuts = db.Column(db.Float, nullable=False)  # percentage
    nutri_score = db.Column(db.String(1), nullable=False)
    numeric_score = db.Column(db.Integer, nullable=False)  # Raw Nutri-Score (-15 to +40)
    simple_score = db.Column(db.Integer, nullable=False)  # Normalized 0-100 score
    is_shared = db.Column(db.Boolean, nullable=False, default=False, server_default='false')  # Whether the food is shared with other users
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who created this food
    creator = db.relationship('User', backref='food_references')
    last_used_quantity = db.Column(db.Float, nullable=False, default=100)  # Last quantity used
    last_used_unit = db.Column(db.String(20), nullable=True)  # Last unit used (e.g., 'egg', 'slice')
    last_used_meal_type = db.Column(db.String(20), nullable=True, default='snack')  # Last meal type selected
    weight_per_unit = db.Column(db.Float, nullable=True, default=100)  # Weight of one unit in grams

    @staticmethod
    def find_similar(food_name, user_id):
        """Find food with similar name that is either shared or owned by the user"""
        return FoodReference.query.filter(
            FoodReference.name.ilike(f"%{food_name}%"),
            sa.or_(
                FoodReference.is_shared == True,
                FoodReference.creator_id == user_id
            )
        ).first()

    def to_dict(self):
        """Convert food reference to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'calories': self.calories,
            'energy_kj': self.energy_kj,
            'protein': self.protein,
            'carbs': self.carbs,
            'sugars': self.sugars,
            'fat': self.fat,
            'saturated_fat': self.saturated_fat,
            'sodium': self.sodium,
            'fiber': self.fiber,
            'fruits_veg_nuts': self.fruits_veg_nuts,
            'nutri_score': self.nutri_score,
            'numeric_score': self.numeric_score,
            'simple_score': self.simple_score,
            'is_shared': self.is_shared,
            'creator': self.creator.username if self.is_shared else None,
            'last_used_quantity': self.last_used_quantity,
            'last_used_unit': self.last_used_unit,
            'last_used_meal_type': self.last_used_meal_type,
            'weight_per_unit': self.weight_per_unit
        }

class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=True, default=None)  # New field for brand
    description = db.Column(db.String(200), nullable=True, default=None)  # New field for description
    meal_type = db.Column(db.String(20), nullable=False, default="snack")  # Field for meal categorization
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)  # Use callable default
    quantity = db.Column(db.Integer, nullable=False, default=100)  # in grams
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Add user association
    
    # Nutritional information (per 100g)
    calories = db.Column(db.Float, nullable=True)
    energy_kj = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    sugars = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    saturated_fat = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)  # in mg
    fiber = db.Column(db.Float, nullable=True)
    fruits_veg_nuts = db.Column(db.Float, nullable=True)  # percentage
    nutri_score = db.Column(db.String(1), nullable=True)
    numeric_score = db.Column(db.Integer, nullable=True)  # Raw Nutri-Score (-15 to +40)
    simple_score = db.Column(db.Integer, nullable=True)  # Normalized 0-100 score

    def get_adjusted_nutrition(self):
        """Get nutrition values adjusted for the actual quantity"""
        # Get base values, defaulting to 0 if None
        base_calories = self.calories or 0
        base_energy_kj = self.energy_kj or 0
        base_protein = self.protein or 0
        base_carbs = self.carbs or 0
        base_sugars = self.sugars or 0
        base_fat = self.fat or 0
        base_saturated_fat = self.saturated_fat or 0
        base_sodium = self.sodium or 0
        base_fiber = self.fiber or 0
        
        # Convert from per 100g to actual quantity
        factor = self.quantity / 100.0
        return {
            'calories': round(base_calories * factor, 1),
            'energy_kj': round(base_energy_kj * factor, 1),
            'protein': round(base_protein * factor, 1),
            'carbs': round(base_carbs * factor, 1),
            'sugars': round(base_sugars * factor, 1),
            'fat': round(base_fat * factor, 1),
            'saturated_fat': round(base_saturated_fat * factor, 1),
            'sodium': round(base_sodium * factor, 1),
            'fiber': round(base_fiber * factor, 1),
            'fruits_veg_nuts': self.fruits_veg_nuts or 0,  # Percentage stays the same
            'grade': self.nutri_score or 'C',  # Letter grade
            'numeric_score': self.numeric_score or 0,  # Raw score
            'simple_score': self.simple_score or 50  # Normalized score
        } 