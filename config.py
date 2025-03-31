import os
from dotenv import load_dotenv
from enum import Enum

# Load environment variables
load_dotenv()

class ModelType(Enum):
    FREE = "flan-t5-base"
    GPT35 = "gpt-3.5-turbo"
    GPT4 = "gpt-4"

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'development-secret-key')  # Add secret key for sessions
    
    # Database settings - always use PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/food_entries')
    # Convert postgres:// to postgresql:// if necessary (Railway uses postgres://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
    HUGGINGFACE_API_BASE_URL = "https://api-inference.huggingface.co/models"

    # Model settings
    CURRENT_MODEL = ModelType.GPT35
    AVAILABLE_MODELS = {
        ModelType.FREE: "Free (FLAN-T5)",
        ModelType.GPT35: "GPT-3.5",
        ModelType.GPT4: "GPT-4"
    }

    # Hugging Face settings
    HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
    
    # Improved Nutrition prompts
    HUGGINGFACE_NUTRITION_PROMPT = """Provide exactly these nutrition values per 100g of {food_name}:
1. calories (kcal)
2. energy in kJ
3. sugars (g)
4. saturated fat (g)
5. total fat (g)
6. sodium (mg)
7. fiber (g)
8. protein (g)
9. percentage of fruits/vegetables/nuts (0-100%)

Format your response as ONLY comma-separated numbers in this exact order:
calories, energy_kJ, sugars, saturated_fat, fat, sodium, fiber, protein, fruits_veg_nuts

Example response for apple:
52, 218, 10.4, 0.0, 0.2, 1, 2.4, 0.3, 100"""

    OPENAI_NUTRITION_SYSTEM_PROMPT = """You are a nutrition database that provides nutritional information for foods.
You MUST format your response as a comma-separated list of numerical values only.
Do not include any labels, units, or explanations.
Round all values to 1 decimal place.
If uncertain about any value, provide a reasonable estimate based on similar foods.

Respond ONLY with numbers in this exact format and order:
calories, energy_kj, sugars, saturated_fat, fat, sodium, fiber, protein, fruits_veg_nuts

Examples:
Apple: 52, 218, 10.4, 0.0, 0.2, 1, 2.4, 0.3, 100
Chicken breast: 165, 690, 0.0, 1.1, 3.6, 74, 0.0, 31.0, 0
Potato chips: 536, 2243, 0.5, 3.4, 34.6, 525, 4.8, 7.0, 10"""

    OPENAI_NUTRITION_PROMPT = """Provide only the numerical nutrition values per 100g for {food_name}.
I need exactly these values in this order:
1. Calories (kcal)
2. Energy (kJ)
3. Sugars (g)
4. Saturated fat (g)
5. Total fat (g)
6. Sodium (mg)
7. Fiber (g)
8. Protein (g)
9. Percentage of fruits/vegetables/nuts content (0-100)

Format as comma-separated numbers ONLY. No text, no labels, no units."""

    # OpenAI settings
    OPENAI_TEMPERATURE = 0.2
    OPENAI_MAX_TOKENS = 75

    # Food type detection prompts
    HUGGINGFACE_FOOD_TYPE_PROMPT = """Analyze this food: "{food_name}"
Extract any quantity information (e.g., "2 eggs", "3 slices") from the description.

Return the food type, unit, weight, and suggested quantity in this exact format: "type|unit|weight|quantity"
Choose type from: beverages, snacks, fruits, vegetables, meats, grains
Choose unit from: ml, g, cookie, piece, slice, unit, cup, tablespoon, egg

Rules for units, weights, and quantities:
- beverages: use "ml" (1 cup = 240ml)
- eggs: use "egg" (standard egg = 50g)
- cookies: use "cookie" (Oreo = 11g, chocolate chip = 16g, standard = 13g)
- crackers: use "unit" (saltine = 3g, graham = 14g, standard = 8g)
- fruits: use "piece" (apple = 180g, banana = 120g, orange = 130g)
- bread: use "slice" (white = 25g, whole wheat = 28g, standard = 26g)
- spreads: use "tablespoon" (15g)
- packaged snacks: use "unit" with specific weight
- everything else: use "g"
- quantity should reflect the number mentioned in the description (e.g., "2 eggs" → quantity = 2)

Example responses:
"beverages|ml|240|1" for a cup of drink
"meats|egg|50|2" for scrambled eggs made with 2 eggs
"snacks|cookie|11|1" for an Oreo cookie
"fruits|piece|180|1" for an apple
"grains|slice|25|3" for 3 slices of white bread"""

    OPENAI_FOOD_TYPE_SYSTEM_PROMPT = """You are a nutrition expert that categorizes foods and determines their natural serving units with precise weights.

You must extract any quantity information from the food description (e.g., "scrambled eggs (I used 2 eggs)" should suggest a serving size of 2 eggs).

You must respond in this exact format: "type|unit|weight|quantity"
where:
- type is one of: beverages, snacks, fruits, vegetables, meats, grains
- unit is one of: ml, g, cookie, piece, slice, unit, cup, tablespoon, egg
- weight is the typical weight in grams (or volume in ml) for one unit
- quantity is the number of units suggested based on the food description (default to 1 if not specified)

For example:
- "scrambled eggs (I used 2 eggs)" should return "meats|egg|50|2" (50g per egg, 2 eggs)
- "apple" should return "fruits|piece|180|1" (180g per apple, 1 apple)

Common weights to use:
Eggs:
- Small egg: 42g
- Medium egg: 50g
- Large egg: 57g
- Standard egg: 50g

Cookies:
- Oreo: 11g
- Chocolate chip: 16g
- Standard cookie: 13g

Fruits:
- Apple: 180g
- Banana: 120g
- Orange: 130g
- Standard fruit: 120g

Bread:
- White bread slice: 25g
- Whole wheat slice: 28g
- Standard slice: 26g

Other:
- Tablespoon: 15g
- Cup (liquid): 240ml
- Cup (cereal): 30g
- Standard snack bar: 35g"""

    OPENAI_FOOD_TYPE_PROMPT = """Analyze this food item: "{food_name}"
Determine its category, natural serving unit, typical weight per unit, and suggested quantity based on the description.

Look for quantity information in the description (e.g., "2 eggs", "3 slices") and use it for the suggested quantity.

Respond with ONLY the category, unit, weight and quantity in this format: "type|unit|weight|quantity"
Example: "snacks|cookie|11|2" for 2 Oreo cookies"""

    # Standard weights for different food items
    STANDARD_WEIGHTS = {
        'cookie': {
            'oreo': 11,
            'chocolate_chip': 16,
            'standard': 13
        },
        'cracker': {
            'saltine': 3,
            'graham': 14,
            'standard': 8
        },
        'fruit': {
            'apple': 180,
            'banana': 120,
            'orange': 130,
            'standard': 120
        },
        'bread': {
            'white': 25,
            'whole_wheat': 28,
            'standard': 26
        },
        'tablespoon': 15,
        'cup': {
            'liquid': 240,
            'cereal': 30,
            'leafy_greens': 15
        }
    }
    
    # Standard serving sizes for different food types
    SERVING_SIZES = {
        'beverages': {
            'unit': 'ml',
            'sizes': [
                {'label': 'Small glass (200ml)', 'value': 200},
                {'label': '✓ Standard glass (250ml)', 'value': 250, 'default': True},
                {'label': 'Large glass (330ml)', 'value': 330},
                {'label': 'Custom volume (ml)', 'value': 'custom'}
            ]
        },
        'snacks': {
            'unit': 'g',
            'sizes': [
                {'label': 'Small portion (25g)', 'value': 25},
                {'label': '✓ Standard portion (50g)', 'value': 50, 'default': True},
                {'label': 'Large portion (100g)', 'value': 100},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        },
        'fruits': {
            'unit': 'g',
            'sizes': [
                {'label': 'Small piece (100g)', 'value': 100},
                {'label': '✓ Medium piece (150g)', 'value': 150, 'default': True},
                {'label': 'Large piece (200g)', 'value': 200},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        },
        'vegetables': {
            'unit': 'g',
            'sizes': [
                {'label': 'Small portion (50g)', 'value': 50},
                {'label': '✓ Standard salad/side (100g)', 'value': 100, 'default': True, 'description': 'A typical side salad or vegetable serving'},
                {'label': 'Medium salad/meal (150g)', 'value': 150, 'description': 'A main course salad or vegetable dish'},
                {'label': 'Large salad/meal (250g)', 'value': 250, 'description': 'A large main course salad or vegetable dish'},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        },
        'meats': {
            'unit': 'g',
            'sizes': [
                {'label': 'Small portion (75g)', 'value': 75},
                {'label': '✓ Standard portion (125g)', 'value': 125, 'default': True, 'description': 'Recommended serving size'},
                {'label': 'Large portion (200g)', 'value': 200},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        },
        'grains': {
            'unit': 'g',
            'sizes': [
                {'label': 'Small portion (30g)', 'value': 30},
                {'label': '✓ Standard portion (60g)', 'value': 60, 'default': True, 'description': 'A typical serving of pasta, rice or grains'},
                {'label': 'Large portion (90g)', 'value': 90},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        },
        'default': {
            'unit': 'g',
            'sizes': [
                {'label': 'Small portion (50g)', 'value': 50},
                {'label': '✓ Standard portion (100g)', 'value': 100, 'default': True},
                {'label': 'Large portion (150g)', 'value': 150},
                {'label': 'Extra large portion (200g)', 'value': 200},
                {'label': 'Custom amount (g)', 'value': 'custom'}
            ]
        }
    }

    @staticmethod
    def get_food_type(food_name):
        """Determine the food type based on the name"""
        food_name = food_name.lower()
        
        # Simple detection based on common keywords
        if any(word in food_name for word in ['water', 'juice', 'milk', 'coffee', 'tea', 'soda']):
            return 'beverages'
        elif any(word in food_name for word in ['apple', 'banana', 'orange', 'berry', 'fruit']):
            return 'fruits'
        elif any(word in food_name for word in ['vegetable', 'carrot', 'broccoli', 'spinach']):
            return 'vegetables'
        elif any(word in food_name for word in ['beef', 'chicken', 'pork', 'fish', 'meat']):
            return 'meats'
        elif any(word in food_name for word in ['bread', 'rice', 'pasta', 'grain', 'cereal']):
            return 'grains'
        elif any(word in food_name for word in ['cookie', 'chip', 'cracker', 'snack', 'candy']):
            return 'snacks'
        else:
            return 'default'

    @staticmethod
    def get_serving_sizes(food_name):
        """Get appropriate serving sizes for a food item"""
        food_type = Config.get_food_type(food_name)
        return Config.SERVING_SIZES.get(food_type, Config.SERVING_SIZES['default']) 