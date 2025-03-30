from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import openai
import requests
from config import Config, ModelType
import re
import hashlib
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')  # For session management
db = SQLAlchemy(app)

# Initialize OpenAI if API key is available
if Config.OPENAI_API_KEY:
    openai.api_key = Config.OPENAI_API_KEY

# Serve static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

class FoodCategory:
    @staticmethod
    def calculate_nutri_score(nutrition_data):
        """Calculate both official Nutri-Score and a simple 0-100 scale score."""
        try:
            # Extract values, defaulting to 0 if not present
            energy_kj = nutrition_data.get('energy_kj', 0)
            sugars = nutrition_data.get('sugars', 0)
            saturated_fat = nutrition_data.get('saturated_fat', 0)
            sodium = nutrition_data.get('sodium', 0)  # in mg
            fruits_veg_nuts = nutrition_data.get('fruits_veg_nuts', 0)  # percentage
            fiber = nutrition_data.get('fiber', 0)
            protein = nutrition_data.get('protein', 0)
            
            # Calculate negative points
            energy_points = 0
            if energy_kj <= 335: energy_points = 0
            elif energy_kj <= 670: energy_points = 1
            elif energy_kj <= 1005: energy_points = 2
            elif energy_kj <= 1340: energy_points = 3
            elif energy_kj <= 1675: energy_points = 4
            elif energy_kj <= 2010: energy_points = 5
            elif energy_kj <= 2345: energy_points = 6
            elif energy_kj <= 2680: energy_points = 7
            elif energy_kj <= 3015: energy_points = 8
            elif energy_kj <= 3350: energy_points = 9
            else: energy_points = 10

            sugar_points = 0
            if sugars <= 4.5: sugar_points = 0
            elif sugars <= 9: sugar_points = 1
            elif sugars <= 13.5: sugar_points = 2
            elif sugars <= 18: sugar_points = 3
            elif sugars <= 22.5: sugar_points = 4
            elif sugars <= 27: sugar_points = 5
            elif sugars <= 31: sugar_points = 6
            elif sugars <= 36: sugar_points = 7
            elif sugars <= 40: sugar_points = 8
            elif sugars <= 45: sugar_points = 9
            else: sugar_points = 10

            sat_fat_points = 0
            if saturated_fat <= 1: sat_fat_points = 0
            elif saturated_fat <= 2: sat_fat_points = 1
            elif saturated_fat <= 3: sat_fat_points = 2
            elif saturated_fat <= 4: sat_fat_points = 3
            elif saturated_fat <= 5: sat_fat_points = 4
            elif saturated_fat <= 6: sat_fat_points = 5
            elif saturated_fat <= 7: sat_fat_points = 6
            elif saturated_fat <= 8: sat_fat_points = 7
            elif saturated_fat <= 9: sat_fat_points = 8
            elif saturated_fat <= 10: sat_fat_points = 9
            else: sat_fat_points = 10

            sodium_points = 0
            sodium_g = sodium / 1000  # Convert mg to g
            if sodium_g <= 0.09: sodium_points = 0
            elif sodium_g <= 0.18: sodium_points = 1
            elif sodium_g <= 0.27: sodium_points = 2
            elif sodium_g <= 0.36: sodium_points = 3
            elif sodium_g <= 0.45: sodium_points = 4
            elif sodium_g <= 0.54: sodium_points = 5
            elif sodium_g <= 0.63: sodium_points = 6
            elif sodium_g <= 0.72: sodium_points = 7
            elif sodium_g <= 0.81: sodium_points = 8
            elif sodium_g <= 0.90: sodium_points = 9
            else: sodium_points = 10

            # Calculate positive points
            fruits_veg_points = 0
            if fruits_veg_nuts <= 40: fruits_veg_points = 0
            elif fruits_veg_nuts <= 60: fruits_veg_points = 1
            elif fruits_veg_nuts <= 80: fruits_veg_points = 2
            else: fruits_veg_points = 5

            fiber_points = 0
            if fiber <= 0.9: fiber_points = 0
            elif fiber <= 1.9: fiber_points = 1
            elif fiber <= 2.8: fiber_points = 2
            elif fiber <= 3.7: fiber_points = 3
            elif fiber <= 4.7: fiber_points = 4
            else: fiber_points = 5

            protein_points = 0
            if protein <= 1.6: protein_points = 0
            elif protein <= 3.2: protein_points = 1
            elif protein <= 4.8: protein_points = 2
            elif protein <= 6.4: protein_points = 3
            elif protein <= 8.0: protein_points = 4
            else: protein_points = 5

            # Calculate total negative and positive points
            negative_points = energy_points + sugar_points + sat_fat_points + sodium_points
            
            # Special protein rule
            if negative_points >= 11 and fruits_veg_nuts < 80:
                protein_points = 0
                
            positive_points = fruits_veg_points + fiber_points + protein_points
            
            # Calculate final score
            final_score = negative_points - positive_points
            
            # Map to letter grade
            if final_score <= -1: letter_grade = 'A'
            elif final_score <= 2: letter_grade = 'B'
            elif final_score <= 10: letter_grade = 'C'
            elif final_score <= 18: letter_grade = 'D'
            else: letter_grade = 'E'
            
            # Calculate simple 0-100 score (normalized)
            # Assuming max possible score is 40 and min is -15
            # Now 100 is the best score (low final_score), 0 is the worst (high final_score)
            simple_score = max(0, min(100, round(100 - ((final_score + 15) * (100/55)))))
            
            return {
                'score': final_score,  # Raw Nutri-Score (-15 to +40)
                'simple_score': simple_score,  # Normalized 0-100 score (100 is best)
                'grade': letter_grade,  # Letter grade A-E
                'components': {
                    'negative_points': {
                        'energy': energy_points,
                        'sugars': sugar_points,
                        'saturated_fat': sat_fat_points,
                        'sodium': sodium_points,
                        'total': negative_points
                    },
                    'positive_points': {
                        'fruits_veg_nuts': fruits_veg_points,
                        'fiber': fiber_points,
                        'protein': protein_points,
                        'total': positive_points
                    }
                }
            }
            
        except Exception as e:
            print(f"Error calculating Nutri-Score: {str(e)}")
            return {
                'score': 0,
                'simple_score': 50,
                'grade': 'C',
                'components': {
                    'negative_points': {'total': 0},
                    'positive_points': {'total': 0}
                }
            }

    @staticmethod
    def get_nutrition_info(food_name, model_type=None):
        """Get comprehensive nutrition info using the specified model."""
        try:
            if model_type is None:
                model_type = Config.CURRENT_MODEL
            print(f"\n=== Getting nutrition info for {food_name} using {model_type} ===")
            
            # Update prompts to request additional nutritional information
            if model_type == ModelType.FREE:
                print("Using Hugging Face model (free tier)")
                nutrition = FoodCategory.huggingface_nutrition(food_name)
            else:
                if Config.OPENAI_API_KEY:
                    print(f"Using OpenAI model ({model_type.value})")
                    nutrition = FoodCategory.openai_nutrition(food_name)
                else:
                    print("No OpenAI API key found, falling back to Hugging Face")
                    nutrition = FoodCategory.huggingface_nutrition(food_name)
            
            if nutrition:
                print(f"Successfully retrieved nutrition values: {nutrition}")
                
                # Convert calories to kJ if needed (1 kcal ≈ 4.184 kJ)
                if 'calories' in nutrition and 'energy_kj' not in nutrition:
                    nutrition['energy_kj'] = nutrition['calories'] * 4.184
                
                # Calculate comprehensive Nutri-Score
                nutri_score = FoodCategory.calculate_nutri_score(nutrition)
                nutrition['nutri_score'] = nutri_score
                print(f"Calculated Nutri-Score: {nutri_score}")
                return nutrition
                
            print("Failed to get nutrition values, using defaults")
            return {
                'calories': 100,
                'energy_kj': 418.4,
                'protein': 5,
                'carbs': 15,
                'sugars': 5,
                'fat': 5,
                'saturated_fat': 2,
                'sodium': 100,
                'fiber': 2,
                'fruits_veg_nuts': 0
            }
            
        except Exception as e:
            print(f"Error in get_nutrition_info: {str(e)}")
            return {
                'calories': 100,
                'energy_kj': 418.4,
                'protein': 5,
                'carbs': 15,
                'sugars': 5,
                'fat': 5,
                'saturated_fat': 2,
                'sodium': 100,
                'fiber': 2,
                'fruits_veg_nuts': 0
            }

    @staticmethod
    def parse_nutrition_values(result):
        """Parse nutrition values from API response, handling various formats."""
        try:
            print(f"Parsing nutrition values from: {result}")
            
            # Initialize nutrition dict with all required fields
            nutrition = {
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
            
            # Split by commas and clean up
            values = [v.strip() for v in result.strip().split(',')]
            
            # Extract numbers from values, handling cases with labels
            def extract_number(value):
                # Remove any text and keep only the number
                number_str = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
                try:
                    return float(number_str)
                except ValueError:
                    return 0

            # The values come in a specific order from the API:
            # calories, energy_kj, sugars, saturated_fat, fat, sodium, fiber, protein, fruits_veg_nuts
            if len(values) >= 9:  # Make sure we have all values
                try:
                    nutrition['calories'] = round(extract_number(values[0]), 1)
                    nutrition['energy_kj'] = round(extract_number(values[1]), 1)
                    nutrition['sugars'] = round(extract_number(values[2]), 1)
                    nutrition['saturated_fat'] = round(extract_number(values[3]), 1)
                    nutrition['fat'] = round(extract_number(values[4]), 1)
                    nutrition['sodium'] = round(extract_number(values[5]), 1)
                    nutrition['fiber'] = round(extract_number(values[6]), 1)
                    nutrition['protein'] = round(extract_number(values[7]), 1)
                    nutrition['fruits_veg_nuts'] = round(extract_number(values[8]), 1)
                    
                    # Estimate carbs (assuming they're mostly from sugars plus some complex carbs)
                    nutrition['carbs'] = round(nutrition['sugars'] * 1.2, 1)  # rough estimate
                    
                    print(f"Parsed nutrition values: {nutrition}")
                    
                    # Validate that we got some non-zero values
                    if all(v == 0 for v in [nutrition['calories'], nutrition['protein'], nutrition['fat']]):
                        print("Warning: All main nutrition values are zero")
                        return None
                        
                    return nutrition
                    
                except (ValueError, IndexError) as e:
                    print(f"Error parsing values: {str(e)}")
                    return None
            else:
                print(f"Not enough values provided: expected 9, got {len(values)}")
                return None
            
        except Exception as e:
            print(f"Error parsing nutrition values: {str(e)}")
            return None

    @staticmethod
    def huggingface_nutrition(food_name):
        """Get nutrition info using Hugging Face API."""
        try:
            print(f"Getting nutrition info from Hugging Face for: {food_name}")
            
            prompt = Config.HUGGINGFACE_NUTRITION_PROMPT.format(food_name=food_name)
            print(f"Prompt: {prompt}")
            
            headers = {"Authorization": f"Bearer {Config.HUGGINGFACE_API_KEY}"}
            api_url = f"{Config.HUGGINGFACE_API_BASE_URL}/models/google/flan-t5-base"
            
            response = requests.post(api_url, headers=headers, json={
                "inputs": prompt,
                "parameters": {"max_length": 100}
            })
            
            if response.status_code == 200:
                result = response.json()[0]["generated_text"]
                print(f"Raw response: {result}")
                
                nutrition = FoodCategory.parse_nutrition_values(result)
                if nutrition:
                    return nutrition
                    
            print(f"Failed to get valid nutrition values from Hugging Face")
            return None
            
        except Exception as e:
            print(f"Error in huggingface_nutrition: {str(e)}")
            return None

    @staticmethod
    def openai_nutrition(food_name):
        """Get nutrition info using OpenAI API."""
        try:
            print(f"Getting nutrition info from OpenAI for: {food_name}")
            
            messages = [
                {"role": "system", "content": Config.OPENAI_NUTRITION_SYSTEM_PROMPT},
                {"role": "user", "content": Config.OPENAI_NUTRITION_PROMPT.format(food_name=food_name)}
            ]
            print(f"Messages: {messages}")
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=100
            )
            
            if response.choices:
                result = response.choices[0].message.content
                print(f"Raw response: {result}")
                
                nutrition = FoodCategory.parse_nutrition_values(result)
                if nutrition:
                    return nutrition
                    
            print(f"Failed to get valid nutrition values from OpenAI")
            return None
            
        except Exception as e:
            print(f"Error in openai_nutrition: {str(e)}")
            return None

class FoodReference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    brand = db.Column(db.String(100), nullable=False, default='Generic')  # Add brand field
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

    @staticmethod
    def find_similar(food_name):
        """Find food with similar name"""
        return FoodReference.query.filter(
            FoodReference.name.ilike(f"%{food_name}%")
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
            'simple_score': self.simple_score
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    salt = db.Column(db.String(64), nullable=False)  # Add salt column
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    food_entries = db.relationship('FoodEntry', backref='user', lazy=True)

    def set_password(self, password):
        # Generate a random salt
        salt = os.urandom(32)
        # Hash password with salt using SHA256
        hash_obj = hashlib.sha256()
        hash_obj.update(salt + password.encode('utf-8'))
        self.password_hash = base64.b64encode(hash_obj.digest()).decode('utf-8')
        self.salt = base64.b64encode(salt).decode('utf-8')

    def check_password(self, password):
        # Get salt from stored value
        salt = base64.b64decode(self.salt.encode('utf-8'))
        # Hash the provided password with stored salt
        hash_obj = hashlib.sha256()
        hash_obj.update(salt + password.encode('utf-8'))
        password_hash = base64.b64encode(hash_obj.digest()).decode('utf-8')
        return self.password_hash == password_hash

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.now().date)  # Use local time
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

with app.app_context():
    # Only create tables if they don't exist
    db.create_all()
    logger.info("Database tables initialized successfully")

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already registered')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    current_user = User.query.get(session['user_id'])
    return render_template('index.html', current_user=current_user)

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models and current model"""
    return jsonify({
        'available_models': {model.value: name for model, name in Config.AVAILABLE_MODELS.items()},
        'current_model': Config.CURRENT_MODEL.value
    })

@app.route('/api/models', methods=['POST'])
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

@app.route('/api/food-references', methods=['GET'])
@login_required
def get_food_references():
    """Get all food references with optional search filter"""
    search = request.args.get('search', '').lower().strip()
    query = FoodReference.query
    
    if search:
        query = query.filter(
            db.or_(
                FoodReference.name.ilike(f"%{search}%"),
                FoodReference.brand.ilike(f"%{search}%")
            )
        )
    
    references = query.order_by(FoodReference.name).all()
    return jsonify([ref.to_dict() for ref in references])

@app.route('/api/food', methods=['POST'])
@login_required
def add_food():
    logger.info("\n=== Adding new food entry ===")
    data = request.json
    food_name = data['name'].lower().strip()  # Normalize food name
    quantity = data.get('quantity', 100)  # Default to 100g if not specified
    brand = data.get('brand', 'Generic').strip()  # Get brand name, default to Generic
    logger.info(f"Food name: {food_name}, Brand: {brand}, Quantity: {quantity}g")
    
    nutrition = None
    
    # Check if nutrition info was manually provided
    manual_nutrition = data.get('nutrition')
    if manual_nutrition:
        logger.info("Using manually provided nutrition info")
        nutrition = manual_nutrition
        
        # Store manual nutrition in reference table
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
            simple_score=nutri_score['simple_score']
        )
        db.session.add(food_ref)
        db.session.commit()
        logger.info(f"Stored manual nutrition in reference table for: {food_name}")
    else:
        # First check if we have this food in our reference database
        reference = FoodReference.find_similar(food_name)
        if reference:
            logger.info("Found food in reference database")
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
            # Use the reference brand if none specified
            if brand == 'Generic':
                brand = reference.brand
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
                    simple_score=nutri_score['simple_score']
                )
                db.session.add(food_ref)
                db.session.commit()
                logger.info(f"Stored AI nutrition in reference table for: {food_name}")
    
    if nutrition:
        if 'nutri_score' not in locals():
            nutri_score = FoodCategory.calculate_nutri_score(nutrition)
        
        # Create new food entry
        entry = FoodEntry(
            name=food_name,
            quantity=quantity,
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

@app.route('/api/food/<int:id>', methods=['DELETE'])
@login_required
def delete_food(id):
    entry = FoodEntry.query.get_or_404(id)
    
    # Check if the entry belongs to the current user
    if entry.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/daily-score')
@login_required
def get_daily_score():
    today = datetime.now().date()
    entries = FoodEntry.query.filter(
        FoodEntry.date == today,
        FoodEntry.user_id == session['user_id']  # Filter by user
    ).all()
    return calculate_period_score(entries)

@app.route('/api/weekly-score')
@login_required
def get_weekly_score():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    entries = FoodEntry.query.filter(
        FoodEntry.date.between(start_date, end_date),
        FoodEntry.user_id == session['user_id']  # Filter by user
    ).all()
    return calculate_period_score(entries)

@app.route('/api/monthly-score')
@login_required
def get_monthly_score():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)
    entries = FoodEntry.query.filter(
        FoodEntry.date.between(start_date, end_date),
        FoodEntry.user_id == session['user_id']  # Filter by user
    ).all()
    return calculate_period_score(entries)

def calculate_period_score(entries):
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
    
    # Calculate nutrition totals using base values and quantity
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
    
    entries_data = []
    for entry in entries:
        # Calculate adjusted nutrition for this entry
        nutrition = entry.get_adjusted_nutrition()
        
        # Add to daily totals using base values and quantity
        factor = entry.quantity / 100.0
        daily_nutrition['calories'] += round((entry.calories or 0) * factor, 1)
        daily_nutrition['energy_kj'] += round((entry.energy_kj or 0) * factor, 1)
        daily_nutrition['protein'] += round((entry.protein or 0) * factor, 1)
        daily_nutrition['carbs'] += round((entry.carbs or 0) * factor, 1)
        daily_nutrition['sugars'] += round((entry.sugars or 0) * factor, 1)
        daily_nutrition['fat'] += round((entry.fat or 0) * factor, 1)
        daily_nutrition['saturated_fat'] += round((entry.saturated_fat or 0) * factor, 1)
        daily_nutrition['sodium'] += round((entry.sodium or 0) * factor, 1)
        daily_nutrition['fiber'] += round((entry.fiber or 0) * factor, 1)
        
        # For fruits/veg/nuts percentage, we need to weight it by the quantity
        if len(entries) == 1:
            daily_nutrition['fruits_veg_nuts'] = entry.fruits_veg_nuts or 0
        else:
            # For multiple entries, calculate weighted average
            total_quantity = sum(e.quantity for e in entries)
            daily_nutrition['fruits_veg_nuts'] = sum(
                (e.fruits_veg_nuts or 0) * (e.quantity / total_quantity) 
                for e in entries
            )
        
        entries_data.append({
            'id': entry.id,
            'name': entry.name,
            'quantity': entry.quantity,
            'nutrition': nutrition,
            'date': entry.date.strftime('%Y-%m-%d')
        })
    
    # Round final totals
    for key in daily_nutrition:
        daily_nutrition[key] = round(daily_nutrition[key], 1)
    
    # Calculate Nutri-Score based on total nutrition
    nutri_score = FoodCategory.calculate_nutri_score(daily_nutrition)
    
    return jsonify({
        'score': nutri_score['score'],  # Raw Nutri-Score (-15 to +40)
        'simple_score': nutri_score['simple_score'],  # Normalized 0-100 score
        'grade': nutri_score['grade'],  # Letter grade A-E
        'entries': entries_data,
        'daily_nutrition': daily_nutrition
    })

if __name__ == '__main__':
    logger.info("Starting Flask application in debug mode")
    app.run(debug=True, port=5001) 