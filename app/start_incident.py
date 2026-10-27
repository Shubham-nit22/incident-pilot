import sys 
import uuid

from app.graph.state import new_incident
from app.persistence import get_graph

DEFAULT = (
    "Someone is trying thousands of passwords against our login endpoint "
    "from 203.0.113.50"
)
text = " ".join(sys.argv[1:]) or DEFAULT

thread_id = f" incident-{uuid.uuid4().hex[:8]}"
config = {
    "configurable": {"thread_id": thread_id},
    "run_name": "incident-run",
    "tags": ["dev", "cli"],
}

with get_graph() as graph:
    graph.invoke(new_incident(text),config)
    snapshot = graph.get_state(config)

    if snapshot.next:
        action = snapshot.tasks[0].interrupts[0].value["action"]
        print(f"\n PAUSED, waiting for approval : {action['name']} on {action['target']}")
        print(f"Reason: {action['reason']}")
        print("\n The program can exit now. when you are ready, run:")
        print(f" python -m app.resume_incident {thread_id}")
    else:
        final = snapshot.values
        print("\n Finished without needing approval.")
        print("Summary:",final["summary"])

        