from langgraph.graph import END,START,StateGraph
from app.graph.nodes import (
    answer,
    classify,
    escalate,
    execute,
    human_approval,
    propose_fix,
    summarize,
    varify
)
from app.graph.routing import (
    after_approval,
    after_classify,
    after_propose,
    after_verify,
)

from app.graph.state import IncidentState


def build_graph(checkpointer=None):
    builder = StateGraph(IncidentState)

    builder.add_node("classify",classify)
    builder.add_node("answer",answer),
    builder.add_node("propose_fix",propose_fix),
    builder.add_node("human_approval",human_approval)
    builder.add_node("execute",execute)
    builder.add_node("verify",varify)
    builder.add_node("summarize",summarize)
    builder.add_node("escalate",escalate)

    # TEMPORARY straight line. Step 6 replaces this with routing,
    # loops and a human approval pause.

    
    #fixed Edges
    builder.add_edge(START,"classify")
    builder.add_edge("execute","verify")
    builder.add_edge("answer",END)
    builder.add_edge("summarize",END)
    builder.add_edge("escalate",END)

    #Conditional Edges
    builder.add_conditional_edges("classify", after_classify,["answer","propose_fix"])
    builder.add_conditional_edges("propose_fix",after_propose,["human_approval","execute"])
    builder.add_conditional_edges(
        "human_approval",after_approval,["execute","propose_fix","escalate"]
    )    
    builder.add_conditional_edges(
        "verify",after_verify,["summarize","propose_fix","escalate"]
    )

    return builder.compile(checkpointer=checkpointer)

