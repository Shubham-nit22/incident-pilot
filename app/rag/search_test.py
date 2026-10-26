from app.rag.embeddings import embed_query
from app.rag.store import connect, search

QUERIES = [
    ("How do i find slow queries in PostgreSQL?","database"),
    ("Checkout API returns 500 errors after a deploy, how to roll back","deployment"),
    ("Users cannot resolve the service name, DNS problem in the cluster","network"),
    ("Thousands of failed login attempts from one IP address","security"),
]

with connect() as conn:
    print("Chunks per category")
    for row in conn.execute("SELECT category, count(*) FROM doc_chunks GROUP BY 1 ORDER BY 1"):
        print(" ",row)

    for question, category in QUERIES:
        print("\nQ:",question)
        for hit in search(conn,embed_query(question),k=3,category=category):
            print(f" {hit['score']} [{hit['category']}] {hit['source']}")
            print("     ",hit["text"][:110].replace("\n"," "))


         