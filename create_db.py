import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load .env from project root
load_dotenv('.env')

# Environment variables (same as used by the app)
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')
HOST = os.getenv('POSTGRES_HOST')
PORT = os.getenv('POSTGRES_PORT', '5432')
TARGET_DB = os.getenv('POSTGRES_DB')  # e.g., "postgre"

if not all([USER, PASSWORD, HOST, TARGET_DB]):
    raise RuntimeError('Missing required PostgreSQL env vars')

# Connect to the default "postgres" database which always exists
conn_str = f"host={HOST} port={PORT} dbname=postgres user={USER} password={PASSWORD}"
conn = psycopg2.connect(conn_str)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Check if the target database already exists
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (TARGET_DB,))
exists = cur.fetchone()
if exists:
    print(f'Database "{TARGET_DB}" already exists.')
else:
    cur.execute(f'CREATE DATABASE "{TARGET_DB}";')
    print(f'Database "{TARGET_DB}" created.')

cur.close()
conn.close()
