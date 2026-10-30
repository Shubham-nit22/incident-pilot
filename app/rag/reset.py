from app.rag.store import connect

with connect() as conn:
    conn.execute("TRUNCATE doc_chunks")
    conn.commit()
print("doc_chunks emptied")