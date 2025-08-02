#!/usr/bin/env bash
# Build script for Render deployment

# Install dependencies
pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p src/database

# Initialize database
python -c "from src.database_sqlite import init_db; init_db()" 