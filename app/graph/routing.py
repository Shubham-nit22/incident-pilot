from app.graph.state import IncidentState

MAX_ATTEMPTS = 3
MAX_REVISIONS = 2

def after_classify(state : IncidentState) -> str:
    if state["intent"] == "info_request":
        return "answer"
    return "execute"

def after_approval(state : IncidentState) -> str:
    if state["approval"] == "approved":
        return "execute"
    if state["revisions"] < MAX_REVISIONS:
        return "propose_fix"
    return "escalate"

def after_propose(state : IncidentState)-> str:
    if state["approval"] == "approved":
        return "execute"
    if state["revisions"] < MAX_REVISIONS:
        return "propose_fix"
    return "escalate"


def after_verify(state : IncidentState) -> str:
    if state["resolved"]:
        return "summarize"
    if state["attempts"] <MAX_ATTEMPTS:
        return "propose_fix"
    return "excalate"

