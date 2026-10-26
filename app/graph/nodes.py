from pydantic import BaseModel
from app.graph.state import Category, IncidentState, Intent
from app.llm import get_llm
from langgraph.types import interrupt
from app.rag.embeddings import embed_query
from app.rag.store import connect,research



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

Incident (category: {category}):
{incident_text}

Relevant runbook excerpts:
{docs}

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
                    docs=format_docs(state["retrieved_docs"]),
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
            "approval": None,
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

def to_text(response) -> str:
     """Models sometimes return a list of part instead of a plan string."""
     content = response.content
     if isinstance(content,str):
          return content
     parts = []
     for part in content:
          if isinstance(part,str):
               parts.append(part)
          elif isinstance(part,dict) and part.get("type") == "text":
               parts.append(part.get("text",""))
     return "".join(parts)


# ------ answer (for information requests) -------



def answer(state: IncidentState) -> dict:
    prompt = (
        "Answer the question using ONLY the runbook excerpts below. "
        "Cite excerpt numbers like [1]. If the excerpts do not contain the answer, "
        "say so clearly instead of guessing.\n\n"
        f"Excerpts:\n{format_docs(state['retrieved_docs'])}\n\n"
        f"Question: {state['incident_text']}"
    )
    text = to_text(get_llm().invoke(prompt))

    urls = sorted({d["source_url"] for d in state["retrieved_docs"] if d.get("source_url")})
    if urls:
        text += "\n\nSources:\n" + "\n".join(f"- {u}" for u in urls)

    return {"summary": text, "history": ["answered information request"]}



# def answer(state : IncidentState) -> dict:
#      response = get_llm().invoke(
#           "Answer this engineering question conscisely (at most 5 sentences) : \n"
#           f"{state['incident_text']}"
#      )
#      return {
#           "summary": to_text(response),
#           "history":["answered information request"],
#      }


# ------------- human approval -------------

def human_approval(state : IncidentState) -> dict:
     # The graph PAUSES here and hands this dictionary to whoever is in charge.
     #  it resumes when someone sends back a dicision.

     decision = interrupt(
          {
               "question":"Approve this action?",
               "incident":state["incident_text"],
               "action":state["proposed_action"],
          }
     )

     approval = decision.get("approval")
     if approval not in ("approved","rejected"):
          approval = "rejected"
     note = decision.get("note")

     entry = f"human {approval}"
     if note:
          entry+= f" : {note}"

     return {
          "approval" : approval,
          "reviwer_note":note,
          "revisions":state["revisions"] + (0 if approval == "approved" else 1),
          "history": [entry],
     }


# ======= summarize ===========

def summarize(state : IncidentState) -> dict:
     prompt = (
          "write a short incident report (4 to 6 lines) with : what happened, "
          "what was done, and the outcome. \n\n"
          f" Incident : {state['incident_text']}\n\n"
          "Event log:\n"+"\n".join(state["history"])
     )
     return{
          "summary":to_text(get_llm().invoke(prompt)),
          "history":["wrote incident summary"],
     }


def escalate(state: IncidentState) -> dict:
    action = state["proposed_action"]
    message = (
        f"ESCALATED to on-call engineer after {state['attempts']} execution "
        f"attempt(s) and {state['revisions']} rejection(s). "
        f"Latest proposal: {action['name']} on {action['target']}."
    )
    return {
        "resolved": False,
        "summary": message,
        "history": ["escalated to on-call engineer"],
    }


def retrieve(state: IncidentState) -> dict:
     category = state["category"]
     try:
          vector = embed_query(state["incident_text"])
          with connect() as conn:
               docs = research(
                    conn,
                    vector, 
                    k=4,
                    category=None if category == "other" else category,
               )
          note = f"retrieved {len(docs)} runbook excerpts"
     except Exception as error:
          docs = []
          note = f" retrieval failed : {repr(error)[:100]}"
     return {"retrieved_docs": docs,"history":[note]}


def format_docs(docs:list[dict])-> str:
     if not docs:
          return "(no runbook excerpts found)"
     return "\n\n".join(
          f"[{i}] ({d['source']}) {d['text']}" for i,d in enumerate(docs,start=1)
     )
