import os
import sys
import psycopg2

is_env_ready = (
    os.environ.get('DATABASE_NAME') and os.environ.get('DATABASE_PASSWORD') and
    os.environ.get('DATABASE_HOST') and os.environ.get('DATABASE_USER')
) is not None

print(f'dbconection.py: is_env_ready={is_env_ready}')

try:
    connection = psycopg2.connect(
        user=os.environ.get('DATABASE_USER'),
        password=os.environ.get('DATABASE_PASSWORD'),
        host=os.environ.get('DATABASE_HOST'),
        port=os.environ.get('DATABASE_PORT'),
        database=os.environ.get('DATABASE_NAME')
    )

    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print(f'dbconection.py connected to: {record}')
    sys.exit(0)
except Exception as e:
    print('DB is not ready', e)
    sys.exit(1)
