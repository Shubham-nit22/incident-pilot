from app.graph.build import build_graph
from app.graph.state import new_incident

graph = build_graph()
state = new_incident(
    "Our checkout API started returning 500 errors right after the latest deploy."
)

for update in graph.stream(state, stream_mode="updates"):
    print(update)
    print()