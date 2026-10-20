from langgraph.graph import END,START,StateGraph
from app.graph.nodes import classify, execute,propose_fix,varify
from app.graph.state import IncidentState


def build_graph():
    builder = StateGraph(IncidentState)

    builder.add_node("classify",classify)
    builder.add_node("propose_fix",propose_fix)
    builder.add_node("execute",execute)
    builder.add_node("verify",varify)

    # TEMPORARY straight line. Step 6 replaces this with routing,
    # loops and a human approval pause.

    
    builder.add_edge(START,"classify")
    builder.add_edge("classify","propose_fix")
    builder.add_edge("propose_fix","execute")
    builder.add_edge("execute","verify")
    builder.add_edge("verify",END)


    return builder.compile()
