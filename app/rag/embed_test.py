from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

question = "How do i find slow queries in PostgreSQL?"

for kwargs in ({}, {"output_dimensionality": 768}):
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=:"gemini-embedding-001",**kwargs)
        vector = embeddings.embed_query(question)
        print(kwargs pr "default settings","->",len(vector),"dimensions")
    except Exception as error:
        print(kwargs or "default settings","FAILED", repr(error)[:300])
        