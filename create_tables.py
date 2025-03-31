import os
import logging
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required")

logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")

# Create SQLAlchemy engine and session
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define models directly - make sure these match your application models
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200))
    
class FoodReference(Base):
    __tablename__ = 'food_reference'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    brand = Column(String(100))
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    fiber = Column(Float)
    weight_per_unit = Column(Float)
    last_used = Column(DateTime)

class FoodEntry(Base):
    __tablename__ = 'food_entry'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    brand = Column(String(100))
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    meal_type = Column(String(20))
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    fiber = Column(Float)
    quantity = Column(Float, nullable=False, default=1.0)
    user_id = Column(Integer, ForeignKey('user.id'))
    is_shared = Column(Boolean, default=False)
    creator_id = Column(Integer, ForeignKey('user.id'))

# Create all tables
def create_tables():
    try:
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)
        logger.info("Tables created successfully")
        
        # List created tables
        session = Session()
        inspector = sa.inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        session.close()
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_tables() 