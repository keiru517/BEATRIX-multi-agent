import os
import json


from langgraph.graph import StateGraph, START, END

# from IPython.display import Image, display
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from dotenv import load_dotenv

from prompt import (
    KERNEL_AGENT_PROMPT,
    META_AGENT_PROMPT,
    CONTEXT_AGENT_PROMPT,
    INU_AGENT_PROMPT,
    KNU_AGENT_PROMPT,
    IDN_AGENT_PROMPT,
    AWX_AGENT_PROMPT,
    WAX_AGENT_PROMPT,
    SEG_AGENT_PROMPT,
    JNY_AGENT_PROMPT,
    INT_AGENT_PROMPT,
    WATCHDOG_AGENT_PROMPT,
)
from states import State

# Load environment variables from .env file
# TODO: need to get from environment variables
load_dotenv()

llm = ChatOpenAI(
    model="gpt-5",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY"),
)

START_NODE = "META_AGENT"
END_NODE = "__end__"
AGENT_ORDER = [
    "META_AGENT",
    "CONTEXT_AGENT",
    "INU_AGENT",
    "KNU_AGENT",
    "IDN_AGENT",
    "AWX_AGENT",
    "WA_AGENT",
    "SEG_AGENT",
    "JNY_AGENT",
    "INT_AGENT",
    "WATCHDOG_AGENT",
]

TOTAL_NODES = len(AGENT_ORDER) + 1  # +1 for KERNEL_AGENT

# Nodes
def kernel_tool(state: State, workflow: StateGraph):
    """
    This tool is used to check existence of all the modules, their order and dependencies.

    Checks:
        • Existence of all required modules
        • Correct module ordering
        • Module dependency validity

    Flow:
        • On success → META_AGENT
        • On failure → WATCHDOG_AGENT (error capture)
    """

    total_nodes = len(workflow.nodes)

    # Get order of nodes by traversing edges from START
    order = []
    edges = workflow.edges  # list of (from_node, to_node) tuples

    edge_map = {from_node: to_node for (from_node, to_node) in edges}

    order = [START_NODE]
    current_node = START_NODE
    while current_node != END_NODE:
        current_node = edge_map.get(current_node)
        if current_node == END_NODE:
            break
        order.append(current_node)

    # TODO: need to do the validation of all the nodes as well

    # Are all modules here and in the right order?
    if total_nodes == TOTAL_NODES and order == AGENT_ORDER:
        return {
            **state,
            "kernel": {
                "system_ready": True,
            },
            # kept this for the future reference
            "node_order": order,
            "total_nodes": total_nodes,
        }
    else:
        return {
            **state,
            "kernel": {
                "system_ready": False,
            },
            # kept this for the future reference
            "node_order": order,
            "total_nodes": total_nodes,
        }


def meta_tool(state: State):
    """Gate function to check if the initialization is successful."""
    print("meta_tool called")
    if state["total_nodes"] == TOTAL_NODES and state["node_order"] == AGENT_ORDER:
        
        print("System ready, calling CONTEXT_AGENT")
        return "Pass"
    print("System not ready, calling WATCHDOG_AGENT")
    return "Fail"


def context_tool(state: State):
    """
    This tool is used to handle the context to convert reduced context vector.
    """
    print("context_tool called")
    messages = [
        SystemMessage(content=CONTEXT_AGENT_PROMPT),
        HumanMessage(content=state["user_message"]),
    ]
    response = llm.invoke(messages)
    return {
        **state,
        "context": response.content,
    }


def inu_tool(state: State):
    """
    This tool is used to calculate individual utility of the user.
    """
    print("inu_tool called")
    messages = [
        SystemMessage(content=INU_AGENT_PROMPT),
        AIMessage(content=state["context"]),
        HumanMessage(content=state["user_message"]),
    ]
    response = llm.invoke(messages)
    print(response.content, type(response.content))
    return {
        **state,
        "utilities": {
            "INU": "INU DATA",
        },
    }


def knu_tool(state: State):
    """
    This tool is used to calculate collective utility of the user.
    """
    print("knu_tool called")
    messages = [
        SystemMessage(content=KNU_AGENT_PROMPT),
        AIMessage(content=state["context"]),
        HumanMessage(content=state["user_message"]),
    ]
    response = llm.invoke(messages)
    return {
        **state,
        "utilities": {
            "KNU": "KNU DATA",
        },
    }


def idn_tool(state: State):
    """
    This tool is used to calculate identity utility of the user.
    """
    print("idn_tool called")
    messages = [
        SystemMessage(content=IDN_AGENT_PROMPT),
        AIMessage(content=state["context"]),
        HumanMessage(content=state["user_message"]),
    ]
    response = llm.invoke(messages)
    return {
        **state,
        "utilities": {
            "IDN": "IDN DATA",
        },
    }


def awareness_tool(state: State):
    """
    This tool is used to calculate awareness of a person.
    """
    print("awareness_tool called")
    # response = llm.invoke(f"Calculate awareness of the following utilities: INU: {state['utilities']['INU']}, KNU: {state['utilities']['KNU']}, IDN: {state['utilities']['IDN']}")
    return {
        **state,
        "awareness": "AWARENESS DATA",
    }


def willingness_tool(state: State):
    """
    This tool is used to calculate readiness to act based on utility, awareness, journey and context.
    """
    print("willingness_tool called")
    # response = llm.invoke(f"Calculate willingness of the following utilities: INU: {state['utilities']['INU']}, KNU: {state['utilities']['KNU']}, IDN: {state['utilities']['IDN']}")
    return {
        **state,
        "willingness": "WILLINGNESS DATA",
    }


def segment_tool(state: State):
    """
    This tool is used to simply classify behavioral segments based on the current outputs of AWX and WAX.
    """
    print("segment_tool called")
    # response = llm.invoke(f"Calculate segment of the following utilities: INU: {state['utilities']['INU']}, KNU: {state['utilities']['KNU']}, IDN: {state['utilities']['IDN']}")
    return {
        **state,
        "segment": "SEGMENT DATA",
    }


def journey_tool(state: State):
    """
    This tool generates a structured path that shows how actors move from one behavioral state to 
    another, based on awareness, willingness, and context.
    """
    print("journey_tool called")
    # response = llm.invoke(f"Calculate journey of the following utilities: INU: {state['utilities']['INU']}, KNU: {state['utilities']['KNU']}, IDN: {state['utilities']['IDN']}")
    return {
        **state,
        "journey": "JOURNEY DATA",
    }


def intervention_tool(state: State):
    """
    This tool converts the behavioral journey outputs into structured intervention guidelines —
    showing what kind of action or measure is most effective to move the actor from 
    the current to the next behavioral phase.
    """
    print("intervention_tool called")
    # response = llm.invoke(f"Calculate intervention of the following utilities: INU: {state['utilities']['INU']}, KNU: {state['utilities']['KNU']}, IDN: {state['utilities']['IDN']}")
    return {
        **state,
        "intervention": "INTERVENTION DATA",
    }


def watchdog_tool(state: State):
    """
    This tool continuously monitors the BEATRIX architecture to ensure that all 
    modules are running correctly, in the right order, and with coherent outputs.
    It doesn't adapt or learn yet — it simply validates structure, integrity, and 
    coherence at runtime.
    """
    print("watchdog_tool called")
    # response = llm.invoke(f"Validate the following intervention: {state['intervention']}")
    return {
        **state,
        "validation": "VALIDATION DATA",
    }


# Build workflow
workflow = StateGraph(State)


# Add nodes
workflow.add_node("KERNEL_AGENT", lambda state: kernel_tool(state, workflow))
# workflow.add_node("META_AGENT", meta_tool)
workflow.add_node("CONTEXT_AGENT", context_tool)
workflow.add_node("INU_AGENT", inu_tool)
workflow.add_node("KNU_AGENT", knu_tool)
workflow.add_node("IDN_AGENT", idn_tool)
workflow.add_node("AWX_AGENT", awareness_tool)
workflow.add_node("JNY_AGENT", journey_tool)
workflow.add_node("WAX_AGENT", willingness_tool)
# TODO: add WTX_AGENT
workflow.add_node("SEG_AGENT", segment_tool)
workflow.add_node("INT_AGENT", intervention_tool)
workflow.add_node("WATCHDOG_AGENT", watchdog_tool)

# Add edges to connect nodes
# KERNEL -> META -> CONTEXT -> INU -> KNU -> IDN -> AWX -> WAX -> SEG -> JNY -> INT -> WATCHDOG
workflow.add_edge(START, "KERNEL_AGENT")
workflow.add_conditional_edges(
    "KERNEL_AGENT",
    meta_tool,
    {"Fail": "WATCHDOG_AGENT", "Pass": "CONTEXT_AGENT"},
)
# workflow.add_edge("META_AGENT", "CONTEXT_AGENT")
# workflow.add_edge("CONTEXT_AGENT", END)

workflow.add_edge("CONTEXT_AGENT", "INU_AGENT")
workflow.add_edge("INU_AGENT", "KNU_AGENT")
workflow.add_edge("KNU_AGENT", "IDN_AGENT")
workflow.add_edge("IDN_AGENT", "AWX_AGENT")
workflow.add_edge("AWX_AGENT", "WAX_AGENT")
# TODO: add WTX_AGENT
workflow.add_edge("WAX_AGENT", "SEG_AGENT")
workflow.add_edge("SEG_AGENT", "JNY_AGENT")
workflow.add_edge("JNY_AGENT", "INT_AGENT")
workflow.add_edge("INT_AGENT", "WATCHDOG_AGENT")
workflow.add_edge("WATCHDOG_AGENT", END)


# Compile
chain = workflow.compile()

# Generate and save PNG visualization
# png_bytes = chain.get_graph().draw_mermaid_png()
# with open("graph_visualization.png", "wb") as f:
#     f.write(png_bytes)
# print("Graph visualization saved to graph_visualization.png")

# Invoke
user_message = "As a budget-conscious college student who knows only a little about investment apps, I’d be willing to try one if it clearly saves me money and shows exactly how it works"
state = chain.invoke({"user_message": user_message})
print(state)
# state = chain.invoke({"topic": "cats"})
# print("Initial joke:")
# print(state["joke"])
# print("\n--- --- ---\n")
# if "improved_joke" in state:
#     print("Improved joke:")
#     print(state["improved_joke"])
#     print("\n--- --- ---\n")

#     print("Final joke:")
#     print(state["final_joke"])
# else:
#     print("Final joke:")
#     print(state["joke"])
