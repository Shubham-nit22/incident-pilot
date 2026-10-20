from app.graph.build import build_graph
from app.graph.state import new_incident

graph = build_graph()

reports = [
    "Our checkout API started returning 500 errors right after the latest deploy.",
    "Someone is trying thousands of passwords agains our login endpoint from 203.0.113.50.",
    "Users in Mumbai cannot reach the site, but Delhi works fine,",
]

for text in reports:
    result = graph.invoke(new_incident(text))
    print(text)
    # print(" intent: ",result["intent"])
    print(" category ",result["category"])
    print(" proposed: ",result["proposed_action"])
    print(" resolved:",result["resolved"])
    print(" history: ")
    for line in result["history"]:
        print("  --",line)
        
    print()
