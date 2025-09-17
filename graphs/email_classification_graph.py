from typing import TypedDict
from langgraph.graph import StateGraph, END


# 1. Define state
class State(TypedDict, total=False):
    step1: str
    step2: str
    step3: str


# 2. Define nodes
def node1(state: State):
    state["step1"] = "Node 1: starting"
    return state


def node2(state: State):
    state["step2"] = f"Node 2: got {state.get('step1')}"
    return state


def node3(state: State):
    state["step3"] = f"Node 3: got {state.get('step2')}"
    return state


# 3. Build graph
workflow = StateGraph(State)

workflow.add_node("node1", node1)
workflow.add_node("node2", node2)
workflow.add_node("node3", node3)

workflow.set_entry_point("node1")
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", "node3")
workflow.add_edge("node3", END)

# 4. Compile
graph = workflow.compile()


if __name__ == "__main__":
    result = graph.invoke({})
    print("\n=== Final Result ===")
    print(result)
