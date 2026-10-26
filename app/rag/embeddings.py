import math

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

DIMENSIONS = 768
_model = None


def _get_model() -> GoogleGenerativeAIEmbeddings : 
    global _model
    if _model is None:
        try:
            _model = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",output_dimensionality=DIMENSIONS
            )
        except Exception:
            _model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    return _model

def _fit(vector: list[float]) -> list[float]:
    """Make every vector exactly 768 numbers long and length 1.

    If the model already returned 768, this only normalizes it. if it returned
    more, we keep the first 768 (Gemini embeddings support this) and normalize.
    """

    v = vector[:DIMENSIONS]
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / norm for x in v]

def embed_documents(texts: list[str]) -> list[list[float]]:
    return [_fit(v) for v in _get_model().embed_documents(texts)]


def embed_query(text: str) -> list[float]:
    return _fit(_get_model().embed_query(text))

