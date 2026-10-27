import hashlib
import re
import time
from pathlib import Path

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from app.rag.embeddings import DIMENSIONS, embed_documents
from app.rag.store import connect, ensure_schema, to_pgvector

RUNBOOKS = Path("data/runbooks")
BATCH_SIZE = 20
PAUSE_SECONDS = 12

md_splitter = RecursiveCharacterTextSplitter.from_language(
    Language.MARKDOWN, chunk_size=1000, chunk_overlap=150
)
txt_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=150
)


def clean(text: str) -> str:
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)  # front matter
    text = re.sub(r"\{\{[<%].*?[>%]\}\}", "", text, flags=re.DOTALL)  # shortcodes
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)  # comments
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_chunks() -> list[dict]:
    chunks = []
    seen_hashes = set()

    for path in sorted(RUNBOOKS.rglob("*")):
        if path.suffix not in (".md", ".txt"):
            continue

        raw = path.read_text(encoding="utf-8")
        first_line, _, body = raw.partition("\n")
        url = None

        if first_line.startswith("SOURCE_URL"):
            url = first_line.removeprefix("SOURCE_URL").strip()
        else:
            body = raw

        splitter = md_splitter if path.suffix == ".md" else txt_splitter

        for i, piece in enumerate(splitter.split_text(clean(body))):
            if len(piece) < 80:
                continue

            digest = hashlib.sha256(piece.encode("utf-8")).hexdigest()

            if digest in seen_hashes:
                continue

            seen_hashes.add(digest)

            chunks.append(
                {
                    "content": piece,
                    "hash": digest,
                    "category": path.parent.name,
                    "source": path.stem,
                    "source_url": url,
                    "index": i,
                }
            )

    return chunks


def embed_with_retry(texts: list[str]) -> list[list[float]]:
    for attempt in range(1, 6):
        try:
            return embed_documents(texts)
        except Exception as error:
            wait = 30 * attempt
            print(
                f" embedding failed ({repr(error)[:120]}). Retrying in {wait}s..."
            )
            time.sleep(wait)

    raise RuntimeError("Embedding kept failing. Try again later.")


def main() -> None:
    chunks = load_chunks()
    print(f" Prepared {len(chunks)} unique chunks from {RUNBOOKS}")

    with connect() as conn:
        ensure_schema(conn)
        existing = {
            r[0]
            for r in conn.execute("SELECT content_hash FROM doc_chunks")
        }
        todo = [c for c in chunks if c["hash"] not in existing]
        print(f"{len(existing)} already stored, {len(todo)} to embed")

        for start in range(0, len(todo), BATCH_SIZE):
            batch = todo[start : start + BATCH_SIZE]
            vectors = embed_with_retry([c["content"] for c in batch])

            for chunk, vector in zip(batch, vectors):
                assert len(vector) == DIMENSIONS

                conn.execute(
                    """
                    INSERT INTO doc_chunks
                    (content, content_hash, category, source, source_url,
                    chunk_index, embedding)
                    VALUES (%s, %s, %s, %s,%s,%s,%s::vector)
                    ON CONFLICT (content_hash) DO NOTHING
                    """,
                    (
                        chunk["content"],
                        chunk["hash"],
                        chunk["category"],
                        chunk["source"],
                        chunk["source_url"],
                        chunk["index"],
                        to_pgvector(vector),
                    ),
                )

            conn.commit()
            print(f" sorted {min(start + BATCH_SIZE, len(todo))}/{len(todo)}")
            time.sleep(PAUSE_SECONDS)

    print("Done. ")


if __name__ == "__main__":
    main()