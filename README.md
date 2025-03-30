# Food Nutrition Score Tracker

A web application that helps users track their food intake and calculate nutrition scores based on the Nutri-Score system. The app uses AI to automatically retrieve nutrition information for foods and provides daily, weekly, and monthly nutrition summaries.

## Features

- User authentication system
- Automatic nutrition information retrieval using AI (GPT-3.5)
- Manual nutrition information entry
- Food reference database with search functionality
- Nutri-Score calculation (A to E grading system)
- Daily, weekly, and monthly nutrition summaries
- Responsive web interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/bru-cab/food_app.git
cd food_app
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
```

5. Initialize the database:
```bash
python app.py
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open a web browser and navigate to:
```
http://localhost:5001
```

3. Register a new account or log in with existing credentials.

4. Start tracking your food intake:
   - Add foods manually or let AI fetch nutrition information
   - View your nutrition scores and summaries
   - Search and reuse previously entered foods

## Configuration

The application can be configured to use different AI models:
- Free (Rule-based)
- GPT-3.5 (Requires OpenAI API key)
- GPT-4 (Requires OpenAI API key)

## License

MIT License 