import sys
from langgraph.types import Command
from app.persistence import get_graph

if len(sys.argv) < 2:
    sys.exit("Usage: python -m app.resume_incident <thread_id>")

thread_id = sys.argv[1]
config = {"configurable":{"thread_id":thread_id}}

with get_graph() as graph:
    snapshot = graph.get_state(config)

    if not snapshot.values:
        sys.exit(f"No saved run found for {thread_id}")

    while snapshot.next:
        action = snapshot.tasks[0].interrupts[0].value["action"]
        print(f"\n Approval needed : {action['name']} on {action['target']} ")
        print(f"Reason: {action['reason']}")

        choice = input("Approve? (y = approve, n= reject): ").strip().lower()
        if choice == "y":
            decision = {"approval":"approved"}
        else:
            note = input("Why are you rejecting it ? ")
            decision = {"approval":"rejected","note":note}


        graph.invoke(Command(resume=decision),config)
        snapshot = graph.get_state(config)

    final = snapshot.values
    print("\n resolved: ",final["resolved"])
    print("summary:\n",final["summary"])
    print("history:")
    for line in final["history"]:
        print("  --",line)

        