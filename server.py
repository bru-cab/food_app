from app import create_app

# Create application instance
flask_app = create_app()

# For Gunicorn to find (both names commonly used)
app = flask_app
application = flask_app

if __name__ == "__main__":
    # For running locally with: python server.py
    app.run(host="0.0.0.0", port=8080) 