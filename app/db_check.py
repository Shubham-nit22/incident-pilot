import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    print(conn.execute("select version()").fetchone()[0])

    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("pgvector version:",conn.execute(
        "select extversion from pg_extension where extname = 'vector'"
    ).fetchone()[0])

    