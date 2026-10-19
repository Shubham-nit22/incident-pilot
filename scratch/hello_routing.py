from typing import TypedDict
from langgraph.graph import StateGraph, START,END

class State(TypedDict):
    text : str

def shoute(state : State) -> dict:
    return {"text":state["text"].upper()}

def whisper(state : State) -> dict:
    return{"text":state["text"].lower()}

def choose(state : State) -> str:
    if len(state["text"]) < 10:
        return "shoute"
    return "whisper"

builder = StateGraph(State)
builder.add_node("shoute",shoute)
builder.add_node("whisper",whisper)

builder.add_conditional_edges(START,choose,["shoute","whisper"])
builder.add_edge("shoute",END)
builder.add_edge("whisper",END)

graph = builder.compile()

print(graph.invoke({"text":"hello"}))
print(graph.invoke({"text":"This is A much longer sentence"}))


print(graph.get_graph().draw_mermaid())

