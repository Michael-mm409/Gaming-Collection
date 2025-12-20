import os

import psycopg2

class Config:
    # Try Docker Compose DB first
    _primary_uri = 'postgresql://Michael:Mickyb22*@db:5432/gamecollection'
    _fallback_uri = 'postgresql://Michael:Mickyb22*@localhost:5433/gamecollection'
    try:
        # Try connecting to Docker DB
        conn = psycopg2.connect(_primary_uri, connect_timeout=2)
        conn.close()
        SQLALCHEMY_DATABASE_URI = _primary_uri
    except Exception:
        # Fallback to local DB
        SQLALCHEMY_DATABASE_URI = _fallback_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
