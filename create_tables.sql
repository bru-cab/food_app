-- Create user table
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(200)
);

-- Create food_reference table
CREATE TABLE IF NOT EXISTS food_reference (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fat FLOAT NOT NULL,
    fiber FLOAT,
    weight_per_unit FLOAT,
    last_used TIMESTAMP
);

-- Create food_entry table
CREATE TABLE IF NOT EXISTS food_entry (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    description TEXT,
    date TIMESTAMP NOT NULL,
    meal_type VARCHAR(20),
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fat FLOAT NOT NULL,
    fiber FLOAT,
    quantity FLOAT NOT NULL DEFAULT 1.0,
    user_id INTEGER REFERENCES "user"(id),
    is_shared BOOLEAN DEFAULT FALSE,
    creator_id INTEGER REFERENCES "user"(id)
);

-- Add alembic_version table for tracking migrations
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert the latest migration version to prevent conflicts
INSERT INTO alembic_version (version_num) 
VALUES ('2d8641e327c2')
ON CONFLICT (version_num) DO NOTHING; 