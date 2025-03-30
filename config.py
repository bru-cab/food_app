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
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///food_entries.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
    HUGGINGFACE_API_BASE_URL = "https://api-inference.huggingface.co/pipeline"

    # Model settings
    CURRENT_MODEL = ModelType.GPT35
    AVAILABLE_MODELS = {
        ModelType.FREE: "Free (FLAN-T5)",
        ModelType.GPT35: "GPT-3.5",
        ModelType.GPT4: "GPT-4"
    }

    # Hugging Face settings
    HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
    
    # Categorization prompts
    HUGGINGFACE_PROMPT = "Categorize {food_name} into one of these categories: whole_foods (fresh fruits, vegetables, meats), minimally_processed (frozen fruits, canned vegetables), processed (packaged snacks, processed meats), fast_food (burgers, fries), or alcohol (beer, wine). Respond with ONLY the category name."
    
    OPENAI_SYSTEM_PROMPT = "You are a nutrition expert that categorizes foods into specific categories. Respond with ONLY the category name."
    OPENAI_CATEGORIZATION_PROMPT = "Categorize {food_name} into one of these categories: whole_foods (fresh fruits, vegetables, meats), minimally_processed (frozen fruits, canned vegetables), processed (packaged snacks, processed meats), fast_food (burgers, fries), or alcohol (beer, wine)."
    
    # Nutrition prompts
    HUGGINGFACE_NUTRITION_PROMPT = """What are the nutritional values per 100g for {food_name}? Include calories, energy in kJ, sugars, saturated fat, total fat, sodium in mg, fiber, protein, and percentage of fruits/vegetables/nuts."""

    OPENAI_NUTRITION_SYSTEM_PROMPT = """You are a nutrition expert that provides detailed nutritional information for foods.
For each food item, provide the following nutritional values per 100g:
- Energy (in both kcal and kJ)
- Total sugars (g)
- Saturated fat (g)
- Total fat (g)
- Sodium (mg)
- Fiber (g)
- Protein (g)
- Percentage of fruits, vegetables, legumes, and nuts (0-100)

Format your response as a comma-separated list of values in this exact order:
calories: X, energy_kj: X, sugars: X, saturated_fat: X, fat: X, sodium: X, fiber: X, protein: X, fruits_veg_nuts: X

Use only numbers, no units. Round all values to 1 decimal place."""

    OPENAI_NUTRITION_PROMPT = """Provide the nutritional information for {food_name} per 100g."""

    # OpenAI settings
    OPENAI_TEMPERATURE = 0.3
    OPENAI_MAX_TOKENS = 50

    # Food categories and their base scores
    FOOD_CATEGORIES = {
        'whole_foods': 100,
        'minimally_processed': 70,
        'processed': 40,
        'fast_food': 20,
        'alcohol': 10
    }

    # Rule-based categorization keywords
    FOOD_KEYWORDS = {
        'whole_foods': [
            'apple', 'banana', 'orange', 'grape', 'berry', 'berries',
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'cod',
            'egg', 'eggs', 'broccoli', 'spinach', 'kale', 'carrot',
            'potato', 'rice', 'quinoa', 'almond', 'walnut'
        ],
        'minimally_processed': [
            'yogurt', 'cheese', 'bread', 'olive oil', 'butter',
            'frozen', 'honey', 'maple syrup', 'milk', 'cream',
            'whole grain', 'roasted'
        ],
        'processed': [
            'canned', 'packaged', 'cereal', 'sauce', 'ketchup',
            'mayonnaise', 'chips', 'crackers', 'cookie', 'snack',
            'processed', 'preserved'
        ],
        'fast_food': [
            'mcdonalds', 'burger king', 'wendys', 'kfc', 'pizza hut',
            'dominos', 'subway', 'taco bell', 'french fries', 'fries',
            'big mac', 'whopper', 'nuggets'
        ],
        'alcohol': [
            'beer', 'wine', 'vodka', 'rum', 'whiskey', 'gin',
            'tequila', 'alcohol', 'alcoholic', 'spirit', 'liquor'
        ]
    }
    
    # Prompts for different models
    OPENAI_SYSTEM_PROMPT = """You are a nutritionist that categorizes foods. 
You MUST categorize plain meats, fish, fruits, and vegetables as whole_foods. 
Only categorize as processed if explicitly mentioned as packaged or canned. 
Respond only with the category name."""

    OPENAI_CATEGORIZATION_PROMPT = """Categorize this single food item: "{food_name}" into exactly one of these categories.

    Rules:
    1. If the food is a plain, unprocessed ingredient (meat, fish, vegetable, fruit), it MUST be categorized as whole_foods
    2. Only categorize as processed if you're certain it's packaged or manufactured
    3. When in doubt about fish or meat, assume it's fresh and categorize as whole_foods
    
    Categories:
    whole_foods:
    - ANY fresh/raw meat (beef, chicken, fish, etc.)
    - ANY fresh fish or seafood (salmon, tuna, cod, etc.)
    - ANY fresh fruit or vegetable
    - Eggs
    - Plain nuts and seeds
    - Plain rice, quinoa
    
    minimally_processed:
    - Natural yogurt, cheese
    - Whole grain bread
    - Olive oil, butter
    - Roasted nuts
    - Frozen fruits/vegetables
    - Honey, maple syrup
    
    processed:
    - Canned foods (only if explicitly mentioned as canned)
    - Packaged snacks
    - Processed cheese products
    - Breakfast cereals
    - Sauces and condiments
    
    fast_food:
    - Chain restaurant foods
    - Fast food burgers
    - Chain pizza
    - French fries
    - Deep fried restaurant foods
    
    alcohol:
    - ANY alcoholic beverage
    - Beer, wine, spirits

    IMPORTANT: If the input is just a type of meat or fish (like 'salmon' or 'chicken'), it MUST be categorized as whole_foods.
    
    Respond with ONLY the category name, nothing else."""

    # Simplified prompt for FLAN-T5
    HUGGINGFACE_PROMPT = """Categorize this food: "{food_name}"
Choose exactly one category from: whole_foods, minimally_processed, processed, fast_food, alcohol

Rules:
- whole_foods: fresh meat, fish, fruits, vegetables, eggs, plain rice
- minimally_processed: yogurt, cheese, bread, olive oil, butter
- processed: canned foods, packaged snacks, cereals, sauces
- fast_food: restaurant foods, burgers, pizza, fries
- alcohol: any alcoholic drink

Important: If it's just meat or fish name, choose whole_foods.
Respond with ONLY the category name.""" 