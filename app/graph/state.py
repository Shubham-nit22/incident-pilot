import operator
from typing import Annotated, Literal, Optional, TypedDict

Intent = Literal["incident","info_request"]
Category = Literal["database","network","deployment","security","other"]

class IncidentState(TypedDict):
    incident_text : str
    intent : Optional[Intent]
    category : Optional[Category]
    retrieved_docs : list[dict]
    proposed_action : Optional[dict]
    approval : Optional[Literal["approved","rejected"]]
    reviewer_note : Optional[str]
    attempts: int
    revisions : int
    resolved : bool
    summary : Optional[str]
    history : Annotated[list[str],operator.add]


def new_incident(text : str) -> IncidentState:
    """create a fresh state with safe defaults for every field"""
    return{
        "incident_text":text,
        "intent":None,
        "category":None,
        "retrieved_docs":[],
        "proposed_action":None,
        "approval":None,
        "reviewer_note":None,
        "attempts":0,
        "revisions":0,
        "resolved":False,
        "summary":None,
        "history":[],
    }

