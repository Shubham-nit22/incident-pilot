from pydantic import BaseModel
from app.graph.state import Category, IncidentState, Intent
from app.llm import get_llm

class Triage(BaseModel):
    intent : Intent
    category : Category

CLASSIFY_PROMPT = """You are an incident triage assistant for an engineering team.

Decide two things about the report below:
-intent : "incident" if something is broken, degraded or under attack and needs action.
  "info_request" if the person only wants information or how-to guidance.
- category : the main area, one of the databas, network, deployment, security, other.

Report:
{incident_text}
"""

def classify(state : IncidentState) -> dict:
    classifier = get_llm().with_structured_output(Triage)
    result = classifier.invoke(
        CLASSIFY_PROMPT.format(incident_text=state["incident_text"])
        )

    # Return the only field this node changes
    return{
        "intent":result.intent,
        "category":result.category,
        "history":[f"classified as{result.intent}/{result.category}"],
    }

