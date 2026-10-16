from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1 . STATE : the shared data every node can read and update
class State(TypedDict):
    text : str

# 2. NODES : plain function, they receive the state and return only what they change
def shout(state : State) -> dict:
    return {"text": state["text"].upper()}

def add_exclaim(state : State) -> dict:
    return {"text":state["text"] + "!"}

#3. BUILD THE GRAPH : register nodes, then connect them with edges
builder = StateGraph(State)
builder.add_node("shout",shout)
builder.add_node("add_exclaim",add_exclaim)

builder.add_edge(START,"shout")
builder.add_edge("shout","add_exclaim")
builder.add_edge("add_exclaim",END)

graph = builder.compile()

#4. RUN IT 
result = graph.invoke({"text":"hello"})
print(result)
