import os
import psycopg2

class Config:
    # 1. Fetch variables from environment, with defaults just in case
    DB_USER = os.environ.get('POSTGRES_USER', 'Michael')
    DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'Mickyb22*')
    DB_HOST = os.environ.get('DB_HOST', '192.168.3.11')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('POSTGRES_DB', 'gamecollection')

    # 2. Construct the URI dynamically
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # 3. Standard Flask/SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')

    # 4. Connection Test (runs when the class is loaded)
    try:
        # Try connecting to the external database
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URI, connect_timeout=2)
        conn.close()
        print(f"--- Database connection to {DB_HOST} successful! ---")
    except Exception as e:
        print(f"--- DATABASE CONNECTION FAILED: {e} ---")
