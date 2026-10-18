import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_llm(temperature : float = 0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_MODEL"],
        temperature=temperature
    )

