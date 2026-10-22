import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
url = os.environ["DATABASE_URL"]
print("Database host:", url.split("@")[-1].split("/")[0])

with psycopg.connect(url) as conn:
    tables = conn.execute(
        "select table_name from information_schema.tables "
        "where table_schema = 'public' order by 1"
    ).fetchall()
    print("Tables:", [t[0] for t in tables])

    if ("checkpoints",) in tables:
        rows = conn.execute(
            "select thread_id, count(*) from checkpoints "
            "group by thread_id order by 2 desc limit 10"
        ).fetchall()
        print("Saved runs (thread_id, checkpoints):")
        for row in rows:
            print("  ", row)