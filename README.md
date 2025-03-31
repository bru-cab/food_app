# Food Nutrition Scoring App

A web application that helps users track and score their food consumption based on nutritional content.

## Project Structure

The application has been refactored into a modular structure:

```
app/
  ├── __init__.py          # Flask app initialization
  ├── models/              # Database models
  │   ├── __init__.py
  │   ├── user.py          # User model with authentication
  │   └── food.py          # FoodEntry and FoodReference models
  ├── routes/              # API endpoints and view routes
  │   ├── __init__.py
  │   ├── auth.py          # Authentication routes
  │   ├── main.py          # Main view routes
  │   └── api.py           # API routes
  ├── services/            # Business logic services
  │   ├── __init__.py
  │   ├── food_category.py # Food categorization and nutrition scoring
  │   └── food_scoring.py  # Scoring calculations
  └── utils/               # Utility functions
      └── __init__.py
config.py                  # Application configuration
run.py                     # Application entry point
```

## Running the Application

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Set up environment variables (see .env.example)

3. Run the application:
```
python run.py
```

The application will be available at http://localhost:5001

## Features

- Food entry tracking with nutritional information
- Automatic nutritional information retrieval using AI models
- Daily, weekly, and monthly nutrition scoring
- Food reference database
- User accounts and authentication
- Sharing food references between users

## API Endpoints

- `/api/models` - Get/set AI model for nutrition analysis
- `/api/food-references` - Food reference database
- `/api/food` - Add/manage food entries
- `/api/daily-score` - Get daily nutrition score
- `/api/weekly-score` - Get weekly nutrition score
- `/api/monthly-score` - Get monthly nutrition score
- `/api/food-type/:name` - Get food type and serving size info

## Configuration

The application can be configured to use different AI models:
- Free (Rule-based)
- GPT-3.5 (Requires OpenAI API key)
- GPT-4 (Requires OpenAI API key)

### Environment Variables

The following environment variables can be configured in your `.env` file:

- `SECRET_KEY`: Flask secret key for session security
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `PORT`: Server port (default: 5001)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Enable debug mode (default: True)
- `FLASK_ENV`: Flask environment (development/production)

See `.env.example` for all available configuration options.

## License

MIT License 