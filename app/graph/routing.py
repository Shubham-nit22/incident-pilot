from app.graph.state import IncidentState

# Loop safety limits: every loop needs an exit
MAX_ATTEMPTS = 3     # how many times we execute a fix before giving up
MAX_REVISIONS = 2    # how many times a human can reject proposals before we escalate


def after_retrieve(state: IncidentState) -> str:
    if state["intent"] == "info_request":
        return "answer"
    return "propose_fix"


def after_propose(state: IncidentState) -> str:
    # The risk label was set by code (the risk table), not by the model
    if state["proposed_action"]["risk"] == "high":
        return "human_approval"
    return "execute"


def after_approval(state: IncidentState) -> str:
    if state["approval"] == "approved":
        return "execute"
    if state["revisions"] < MAX_REVISIONS:
        return "propose_fix"      # loop back with the reviewer's note
    return "escalate"


def after_verify(state: IncidentState) -> str:
    if state["resolved"]:
        return "summarize"
    if state["attempts"] < MAX_ATTEMPTS:
        return "propose_fix"      # loop back and try something else
    return "escalate"