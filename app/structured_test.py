from typing import Literal
from pydantic import BaseModel
from app.llm import get_llm

class Triage(BaseModel):
    intent : Literal["incident","info_request"]
    category : Literal["database","network","deployment","security","other"]

llm = get_llm()
classifier = llm.with_structured_output(Triage)

reports = [
    "Our checkout API started returning 500 errors right after the latest deploy.",
    "How do i check which queries are slow in PostgresSQL ?",
    "Someone is trying thousand of passwords against our login endpoint.",
]

for text in reports:
    print(text)
    print(" -> ",classifier.invoke(f"Classify this report : \n{text}"))
    