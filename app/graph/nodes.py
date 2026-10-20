from pydantic import BaseModel
from app.graph.state import Category, IncidentState, Intent
from app.llm import get_llm

from app.tools.simulated_tools import (
    ACTIONS,
    ActionName,
    check_health,
    get_risk,
    run_action,
)


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

class FixProposal(BaseModel):
    name : ActionName
    target : str
    reason : str

ACTION_LIST = "\n".join(
    f"- {name} : {info['description']}" for name, info in ACTIONS.items()
)

PROPOSE_PROMPT = """ You are an incident response assistant.
Propose exactly ONE action to fix the incident.

Available actions : 
{action_list}

Incident (category : {category}):
{incident_text}

{extra_context}

choose the single most appropriate action. for the target, use the service name
or IP address from the report; if none is given, use "unknown-service".
Give a one-sentence reason.
"""

def propose_fix(state : IncidentState)-> dict:
    extra = []
    if state["revisions"] > 0 and state["reviewer_note"]:
        extra.append(
            f" A human reviewer rejected the prevous proposal : {state['reviewer_note']}\n"
            "Propose a different action. "
        )
    if state["attempts"] > 0:
            extra.append(
                "The previous action did not fix the problem. what happened so far : \n"
                + "\n".join(state["history"])
            )

    prompt = PROPOSE_PROMPT.format(
            action_list = ACTION_LIST,
            category = state['category'],
            incident_text = state["incident_text"],
            extra_context = "\n\n".join(extra),
        )
    proposal = get_llm().with_structured_output(FixProposal).invoke(prompt)

    action = {
            "name" : proposal.name,
            "target":proposal.target,
            "reason":proposal.reason,
            "risk":get_risk(proposal.name),
        }
    return{
            "proposed_action":action,
            "history":[
                f"proposed {proposal.name} or {proposal.target} (risk: {action['risk']})"
            ],
        }


def execute(state : IncidentState) -> dict:
    action = state["proposed_action"]
    result = run_action(action['name'],action['target'])
    return{
        "attempts":state["attempts"]+1,
        "history":[f"executed {action['name']} on {action['target']} : {result['message']}"],
    }

def varify(state : IncidentState) -> dict:
    action = state["proposed_action"]
    healthy = check_health(action["target"])
    return { 
        "resolved" : healthy,
        "history" : [f"verification {'passed' if healthy else 'failed'}"],
    }