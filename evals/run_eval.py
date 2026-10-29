import os,sys,time,uuid
import subprocess

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langsmith import Client

import app.tools.simulated_tools as simulated_tools
from app.graph.build import build_graph
from app.graph.state import new_incident
from evals.evaluators import (
    action_acceptable,
    category_correct,
    finished_ok,
    grounded,
    high_risk_gated,
    intent_correct,
    retrieval_on_topic,
)



load_dotenv()

# Make run repeatable: every simulated fix passes verification.

simulated_tools.HEALTH_SUCCESS_RATE = 1.0
PAUSE_SECONDS = 3

graph = build_graph(checkpointer=InMemorySaver())

EVALUATORS = [
    intent_correct,
    category_correct,
    action_acceptable,
    high_risk_gated,
    finished_ok,
    retrieval_on_topic,
    grounded,
]

def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git","rev-parse","--short","HEAD"],text=True).strip()
    except Exception:
        return None

    
def run_graph(inputs : dict) -> dict:
    """Run one incident A fake reviewer approves every pause."""
    time.sleep(PAUSE_SECONDS)
    config = {
        "configurable":{"thread_id":f"eval-{uuid.uuid4().hex[:8]}"},
        "tags":["eval"],
    }
    try:
        graph.invoke(new_incident(inputs["text"]),config)
        snapshot = graph.get_state(config)

        pauses = 0
        while snapshot.next and pauses < 5:
            graph.invoke(
                Command(resume = {"approval":"approved","note":"auto-approved in evaluation"}),
                config,
            )
            snapshot = graph.get_state(config)
            pauses += 1

        state = snapshot.values
        action = state.get("proposed_action")
        docs = state.get("retrieved_docs",[])

        return {
            "intent" : state.get("intent"),
            "category": state.get("category"),
            "proposed_action_name": action["name"] if action else None,
            "risk": action["risk"] if action else None,
            "resolved":state.get("resolved"),
            "summary": state.get("summary"),
            "history": state.get("history",[]),
            "retrieved_sources": [d["source"] for d in docs],
            "retrieved_categories": [d["category"] for d in docs],
            "retrieved_texts":[d["text"] for d in docs],
        }
    except Exception as error:
     return {
        "error": repr(error)[:300],
        "intent": None,
        "category": None,
        "proposed_action_name": None,
        "resolved": False,
        "summary": None,
        "history": [],
        "retrieved_sources": [],
    }


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "dev"
    prefix  = sys.argv[2] if len(sys.argv)>2 else "baseline"
    # limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

    # dataset_name = f"incident-triage-{split}"
    # client = Client()
    # data = client.list_examples(dataset_name=dataset_name, limit=limit) if limit else dataset_name
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    only = sys.argv[4] if len(sys.argv) > 4 else None   # "info_request" or "incident"

    dataset_name = f"incident-triage-{split}"
    client = Client()

    data = dataset_name
    if limit or only:
        examples = list(client.list_examples(dataset_name=dataset_name))
        if only:
            examples = [e for e in examples if e.outputs["intent"] == only]
        data = examples[:limit] if limit else examples


    results = client.evaluate(
        run_graph,
        data = data,
        evaluators=EVALUATORS,
        experiment_prefix=prefix,
        max_concurrency=1,
        metadata={
            "model": os.environ.get("GEMINI_MODEL"),
            "split":split,
            "git_commit":git_commit()},
    )

    totals : dict[str,list[float]] ={}
    try:
        for row in results:
            for item in row["evaluation_results"]["results"]:
                if item.score is None:
                    continue
                totals.setdefault(item.key, []).append(float(item.score))
        print("\nSummary")
        for key, scores in totals.items():
            print(f"  {key:20s} {sum(scores) / len(scores):.0%}  ({len(scores)} examples)")
    except Exception as error:
        print("Could not print a summary here; open the experiment in LangSmith.", repr(error)[:120])


if __name__ == "__main__":
    main()


