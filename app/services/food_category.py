import requests
import openai
from config import Config, ModelType
import logging
import re

logger = logging.getLogger(__name__)

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
            logger.error(f"Error calculating Nutri-Score: {str(e)}")
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
            logger.info(f"\n=== Getting nutrition info for {food_name} using {model_type} ===")
            
            # Update prompts to request additional nutritional information
            if model_type == ModelType.FREE:
                logger.info("Using Hugging Face model (free tier)")
                nutrition = FoodCategory.huggingface_nutrition(food_name)
            else:
                if Config.OPENAI_API_KEY:
                    logger.info(f"Using OpenAI model ({model_type.value})")
                    nutrition = FoodCategory.openai_nutrition(food_name)
                else:
                    logger.info("No OpenAI API key found, falling back to Hugging Face")
                    nutrition = FoodCategory.huggingface_nutrition(food_name)
            
            if nutrition:
                logger.info(f"Successfully retrieved nutrition values: {nutrition}")
                
                # Convert calories to kJ if needed (1 kcal ≈ 4.184 kJ)
                if 'calories' in nutrition and 'energy_kj' not in nutrition:
                    nutrition['energy_kj'] = nutrition['calories'] * 4.184
                
                # Calculate comprehensive Nutri-Score
                nutri_score = FoodCategory.calculate_nutri_score(nutrition)
                nutrition['nutri_score'] = nutri_score
                logger.info(f"Calculated Nutri-Score: {nutri_score}")
                return nutrition
                
            logger.info("Failed to get nutrition values, using defaults")
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
            logger.error(f"Error in get_nutrition_info: {str(e)}")
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
            logger.info(f"Parsing nutrition values from: {result}")
            
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
            
            # Clean up the result
            # Remove any text that's not part of the comma-separated values
            result = result.strip()
            
            # Extract just the numbers in a comma-separated list
            # This regex finds sequences of digits, decimal points, and minus signs separated by commas
            matches = re.findall(r'[-\d.]+', result)
            
            # If we have the expected number of values
            if len(matches) >= 9:
                try:
                    nutrition['calories'] = round(float(matches[0]), 1)
                    nutrition['energy_kj'] = round(float(matches[1]), 1)
                    nutrition['sugars'] = round(float(matches[2]), 1)
                    nutrition['saturated_fat'] = round(float(matches[3]), 1)
                    nutrition['fat'] = round(float(matches[4]), 1)
                    nutrition['sodium'] = round(float(matches[5]), 1)
                    nutrition['fiber'] = round(float(matches[6]), 1)
                    nutrition['protein'] = round(float(matches[7]), 1)
                    nutrition['fruits_veg_nuts'] = round(float(matches[8]), 1)
                    
                    # Estimate carbs (assuming they're mostly from sugars plus some complex carbs)
                    nutrition['carbs'] = round(nutrition['sugars'] * 1.2, 1)  # rough estimate
                    
                    logger.info(f"Parsed nutrition values: {nutrition}")
                    
                    # Basic validation - check if we have reasonable numbers
                    if nutrition['calories'] < 1 or nutrition['calories'] > 1000:
                        logger.info(f"Calories value seems unreasonable: {nutrition['calories']}")
                        
                    # Reject results where all main nutrients are zero
                    if all(v == 0 for v in [nutrition['calories'], nutrition['protein'], nutrition['fat']]):
                        logger.info("Warning: All main nutrition values are zero")
                        return None
                        
                    return nutrition
                    
                except (ValueError, IndexError) as e:
                    logger.error(f"Error parsing values: {str(e)}")
                    return None
            else:
                # If we didn't get enough values, try to extract them using the old method
                values = [v.strip() for v in result.strip().split(',')]
                
                # Extract numbers from values, handling cases with labels
                def extract_number(value):
                    # Remove any text and keep only the number
                    number_str = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
                    try:
                        return float(number_str)
                    except ValueError:
                        return 0
                
                if len(values) >= 9:
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
                        
                        # Estimate carbs
                        nutrition['carbs'] = round(nutrition['sugars'] * 1.2, 1)
                        
                        logger.info(f"Parsed nutrition values using fallback method: {nutrition}")
                        
                        # Basic validation
                        if all(v == 0 for v in [nutrition['calories'], nutrition['protein'], nutrition['fat']]):
                            logger.info("Warning: All main nutrition values are zero")
                            return None
                            
                        return nutrition
                    except (ValueError, IndexError) as e:
                        logger.error(f"Error parsing values with fallback method: {str(e)}")
                        return None
                else:
                    logger.info(f"Not enough values provided: expected 9, got {len(values)}")
                    return None
            
        except Exception as e:
            logger.error(f"Error parsing nutrition values: {str(e)}")
            return None

    @staticmethod
    def huggingface_nutrition(food_name):
        """Get nutrition info using Hugging Face API."""
        try:
            logger.info(f"Getting nutrition info from Hugging Face for: {food_name}")
            
            prompt = Config.HUGGINGFACE_NUTRITION_PROMPT.format(food_name=food_name)
            logger.info(f"Prompt: {prompt}")
            
            headers = {"Authorization": f"Bearer {Config.HUGGINGFACE_API_KEY}"}
            api_url = f"{Config.HUGGINGFACE_API_BASE_URL}/models/google/flan-t5-base"
            
            response = requests.post(api_url, headers=headers, json={
                "inputs": prompt,
                "parameters": {
                    "max_length": 150,
                    "temperature": 0.2,
                    "num_return_sequences": 1,
                    "do_sample": True
                }
            })
            
            if response.status_code == 200:
                result = response.json()[0]["generated_text"]
                logger.info(f"Raw response: {result}")
                
                nutrition = FoodCategory.parse_nutrition_values(result)
                if nutrition:
                    return nutrition
                    
            logger.info(f"Failed to get valid nutrition values from Hugging Face")
            return None
            
        except Exception as e:
            logger.error(f"Error in huggingface_nutrition: {str(e)}")
            return None

    @staticmethod
    def openai_nutrition(food_name):
        """Get nutrition info using OpenAI API."""
        try:
            logger.info(f"Getting nutrition info from OpenAI for: {food_name}")
            
            messages = [
                {"role": "system", "content": Config.OPENAI_NUTRITION_SYSTEM_PROMPT},
                {"role": "user", "content": Config.OPENAI_NUTRITION_PROMPT.format(food_name=food_name)}
            ]
            logger.info(f"Messages: {messages}")
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=Config.OPENAI_TEMPERATURE,
                max_tokens=Config.OPENAI_MAX_TOKENS,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            if response.choices:
                result = response.choices[0].message.content
                logger.info(f"Raw response: {result}")
                
                nutrition = FoodCategory.parse_nutrition_values(result)
                if nutrition:
                    return nutrition
                    
            logger.info(f"Failed to get valid nutrition values from OpenAI")
            return None
            
        except Exception as e:
            logger.error(f"Error in openai_nutrition: {str(e)}")
            return None 