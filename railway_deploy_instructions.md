# Railway Deployment Guide

## Prerequisites
- A Railway account
- Your GitHub repository with the application code

## Steps

### 1. Set Up Your Repository
Make sure your repository includes:
- wsgi.py (created above)
- Updated Procfile
- requirements.txt with all dependencies
- setup_db.py for database setup

### 2. Create a New Project in Railway
1. Log in to [Railway](https://railway.app/)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Select your repository
5. Click "Deploy Now"

### 3. Add PostgreSQL Database
1. In your project, click "New"
2. Select "Database"
3. Choose "PostgreSQL"
4. Wait for the database to provision

### 4. Configure Environment Variables
Go to the "Variables" tab of your project and add:
- `SECRET_KEY`: Generate a secure random string
- `OPENAI_API_KEY`: Your OpenAI API key
- `HUGGINGFACE_API_KEY`: Your Hugging Face API key (if used)
- `FLASK_APP=wsgi.py`
- `FLASK_ENV=production`

Railway automatically adds:
- `DATABASE_URL`: Connection string to your PostgreSQL database
- `PORT`: The port your app should listen on

### 5. Deployment Settings
1. Go to the "Settings" tab of your service
2. Make sure the "Start Command" matches your Procfile:
   ```
   flask db upgrade && gunicorn --bind 0.0.0.0:$PORT wsgi:app
   ```

### 6. Monitor Deployment
1. Go to the "Deployments" tab to monitor the build process
2. Check logs for any errors

### 7. Manually Set Up Database If Needed
If automatic migrations fail, connect to your database and run migrations manually:

1. Get the database connection details from the Railway dashboard
2. Use a PostgreSQL client (like pgAdmin or psql) to connect
3. Run SQL commands to create your tables:

```sql
-- Example structure, adjust to match your models
CREATE TABLE IF NOT EXISTS user (
  id SERIAL PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS food_reference (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  brand VARCHAR(100),
  calories FLOAT NOT NULL,
  protein FLOAT NOT NULL,
  carbs FLOAT NOT NULL,
  -- Add other columns as needed
);

-- Add other tables as needed
```

### 8. Access Your Application
Once deployment is successful, Railway will provide a URL to access your application.

## Troubleshooting
- Check logs for specific error messages
- Verify environment variables are set correctly
- Ensure database connection is working
- Check if your application is importing modules correctly 