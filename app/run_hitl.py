from langgraph.checkpoint import InMemorySaver
from langgraph.types import Command

from app.graph.build import build_graph
from app.graph.state import new_incident

graph = build_graph(checkpointer=InMemorySaver())

def run_incident(text : str,thread_id : str)-> dict:
    #Thread id = the key that identifies this one run's saved state
    config = {"configurable":{"thread_id":thread_id}}
    graph.invoke(new_incident(text),config)

    #while the graph is paused, ask the human what to do
    snapshot = graph.get.state(config)
    while snapshot.next:
        request = snapshot.tasks[0].interrupts[0].value
        action = request["action"]
        print(f"\n >>> PAUSED. approval needed : {action['name']} on {action['target']}")
        print(f"  reason: {action['reason']}")

        choice = input(" Approve? (y = approve, n= reject): ").strip().lower()
        if choice == "y":
            decision = {"approval":"approved"}
        else:
            note = input(" why are you rejecting it? ")
            decision= {"approval": "rejected","note":note}

        graph.invoke(Command(resume=decision),config)
        snapshot = graph.get_state(config)

    return snapshot.values

reports = [
    "How do I find slow queries in PostgresSQL?",
    "Out checkout API started returning 500 errors right after the latest deploy.",
    "Someone is trying thousand of password against our login endpoint from 203,0.113.50.",
]

for i, text in enumerate(reports):
    print("=" * 70)
    print("REPORT:",text)
    final = run_incident(text,thread_id=f"incident-{i}")
    print("\n category: ",final["category"])
    print(" resolved:",final["resolved"])
    print(" summary:\n", final["summary"])
    print(" history:")
    for line in final["history"]:
        print("     --",line)

        