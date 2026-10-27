import os

import psycopg
from dotenv import load_dotenv

from app.rag.embeddings import DIMENSIONS
from langsmith import traceable

load_dotenv()


def connect() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"])


def to_pgvector(vector: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vector) + "]"


SCHEMA = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    f"""
    CREATE TABLE IF NOT EXIST doc_chucks (
    id           BIGSERIAL PRIMARY KEY,
    content      TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    category     TEXT NOT NULL,
    source       TEXT NOT NULL,
    source_url   TEXT,
    chunk_index  INT NOT NULL
    embedding    vector({DIMENSIONS}) NOT NULL
    )
""",
    "CREATE INDEX IF NOT EXISTS doc_chunk_category_idx ON doc_chunks (category)",
]


def ensure_schema(conn: psycopg.Connection) -> None:
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()



@traceable(
    name="pgvector_search",
    run_type="retriever",
    process_inputs=lambda inputs: {"k": inputs.get("k"), "category": inputs.get("category")},
)
def research(conn, query_vector, k: int = 4, category : str | None= None) -> list[dict]:
    """Return the k most similar chunks, optionally only from one category."""
    vec = to_pgvector(query_vector)
    sql = (
        "SELECT content, source, source_url, category, "
        "1 - (embedding <=> %s::vector) AS score FROM doc_chunks"
    )
    params: list = [vec]
    if category:
        sql+= " WHERE category = %s"
        params.append(category)
    sql+= " ORDER BY embedding <=> %s::vector LIMIT %s"
    params += [vec,k]

    rows = conn.execute(sql,params).fetchall()
    return [
        {
            "text":r[0],
            "source":r[1],
            "source_url":r[2],
            "category":r[3],
            "score":round(float(r[4]),3),
        }
        for r in rows
    ]