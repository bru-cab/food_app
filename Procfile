web: python -c "from app import db; db.drop_all(); db.create_all()" && gunicorn --bind 0.0.0.0:$PORT app:app 