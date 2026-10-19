from langgraph.graph import END,START,StateGraph
from app.graph.nodes import classify
from app.graph.state import IncidentState


def build_graph():
    builder = StateGraph(IncidentState)

    builder.add_node("classify",classify)
    builder.add_edge(START,"classify")
    builder.add_edge("classify",END)

    return builder.compile()
