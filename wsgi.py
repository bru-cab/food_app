from app import create_app

# For Gunicorn
application = create_app()
# For compatibility 
app = application

if __name__ == "__main__":
    app.run() 