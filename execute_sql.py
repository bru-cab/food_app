import os
import logging
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_sql_file():
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
        
        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read SQL file
        with open('create_tables.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL
        logger.info("Executing SQL to create tables")
        cursor.execute(sql)
        logger.info("SQL executed successfully")
        
        # List created tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        logger.info(f"Tables in database: {table_names}")
        
        # Close connection
        cursor.close()
        conn.close()
        logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        raise

if __name__ == "__main__":
    execute_sql_file() 