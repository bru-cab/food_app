from app import create_app, init_db

application = create_app()

# Initialize database tables within app context
init_db(application)

# For backwards compatibility
app = application

if __name__ == "__main__":
    application.run() 