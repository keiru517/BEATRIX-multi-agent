import os
import json
from datetime import datetime

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
    WTX_AGENT_PROMPT,
    SEG_AGENT_PROMPT,
    JNY_AGENT_PROMPT,
    INT_AGENT_PROMPT,
    WATCHDOG_AGENT_PROMPT,
)
from states import State
from states.inu_state import INUState
from states.knu_state import KNUState
from states.meta_state import MetaState
from states.wtx_state import WTXState

# Load environment variables from .env file
# TODO: need to get from environment variables
load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
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
        if current_node == END_NODE or current_node is None:
            break
        order.append(current_node)

    # TODO: need to do the validation of all the nodes as well

    # Are all modules here and in the right order?
    if total_nodes == TOTAL_NODES and order == AGENT_ORDER:
        print("kernel_tool: all modules are here and in the right order")
        return {
            **state,
            "kernel": {
                "system_ready": True,
                "agents_registered": order,
                "version_info": "v1.0",  # TODO: need to get the version info from the kernel
                "kernel_timestamp": datetime.now().isoformat(),
            },
        }
    else:
        print("kernel_tool: all modules are not here or in the right order")
        return {
            **state,
            "kernel": {
                "system_ready": True,
                "agents_registered": order,
                "version_info": "v1.0",  # TODO: need to get the version info from the kernel
                "kernel_timestamp": datetime.now().isoformat(),
            },
        }


def meta_tool(state: State):
    """Gate function to check if the initialization is successful."""

    input_data = (
        f"Here is the input data.\n"
        f"Kernel status: {state['kernel']['system_ready']}\n"
        f"Agents registered: {', '.join(state['kernel']['agents_registered'])}\n"
        f"Version info: {state['kernel']['version_info']}\n"
        f"Kernel timestamp: {state['kernel']['kernel_timestamp']}"
    )

    structured_llm = llm.with_structured_output(MetaState)
    response = structured_llm.invoke(
        [
            SystemMessage(content=META_AGENT_PROMPT),
            HumanMessage(content=input_data),
        ]
    )

    return {
        **state,
        "meta": {
            **response,
        },
    }


def context_tool(state: State):
    """
    This tool is used to Transform a contextual input (provided as structured JSON) into
    a simplified 4-dimensional context modulation vector.
    """
    print("CONTEXT_AGENT called")

    input_data = {
        "kernel_status": state["meta"]["kernel_status"],
        "user_message": state["user_message"],
        # TODO: this data might comes from the user at the beginning.
        "environment": {
            "institutional": 0.82,
            "social": 0.58,
            "informational": "medium",
            "complexity": "very high",
        },
    }

    response = llm.invoke(
        [
            SystemMessage(content=CONTEXT_AGENT_PROMPT),
            HumanMessage(content=json.dumps(input_data)),
        ]
    )
    content = json.loads(response.content)

    return {
        **state,
        "context": {
            **content,
        },
    }


def inu_tool(state: State):
    """
    This tool is used to calculate individual utility of the user.
    """

    # TODO: if context_state != active, do not calculation
    # TODO: if cqi < 0.3, trigger WATCHDOG_AGENT

    input_data = f"Here is the context vector from KON: {json.dumps(state['context']['context_vector'])} and CQI: {state['context']['cqi']}"
    messages = [
        SystemMessage(content=INU_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(INUState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "inu": {
            **response,
        },
    }


def knu_tool(state: State):
    """
    This tool is used to calculate collective utility of the user.
    """

    print("KNU_AGENT called")

    input_data = f"Here is the INU data and context vector from KON: {json.dumps(state['inu'])} and {json.dumps(state['context']['context_vector'])}"
    messages = [
        SystemMessage(content=KNU_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(KNUState)
    response = structured_llm.invoke(messages)
    return {
        **state,
        "knu": {
            **response,
        },
    }


def idn_tool(state: State):
    """
    This tool is used to describe how identity, belonging, and self-concept contribute to value creation.
    """

    print("IDN_AGENT called")

    input_data = f"Here is the INU data, KNU data and KON data: {json.dumps(state['inu'])} and {json.dumps(state['knu'])} and {json.dumps(state['context'])}"
    messages = [
        SystemMessage(content=IDN_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    response = llm.invoke(messages)
    content = json.loads(response.content)

    return {
        **state,
        "idn": {
            **content,
        },
    }


def awareness_tool(state: State):
    """
    This tool is used to estimate the level of awareness based on individual utility
    (INU), collective alignment (KNU), and contextual stability (CQI).
    """

    print("AWX_AGENT called")

    input_data = f"""Here is the input data.
    inu: {state['inu']['inu']}
    alignment_index: {state['knu']['alignment_index']}
    cqi: {state['context']['cqi']}
    kernel_status: {state['meta']['kernel_status']}
    """
    messages = [
        SystemMessage(content=AWX_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    response = llm.invoke(messages)
    content = json.loads(response.content)

    return {
        **state,
        "awx": {
            **content,
        },
    }


def willingness_tool(state: State):
    """
    This tool is used to estimate an actor's readiness to act upon their awareness.
    """
    print("WAX_AGENT called")

    input_data = f"""Here is the input data.
    awareness_level: {json.dumps(state['awx']['awareness_level'])}
    inu: {json.dumps(state['inu']['inu'])}
    cqi: {state['context']['cqi']}
    kernel_status: {state['meta']['kernel_status']}
    """
    messages = [
        SystemMessage(content=WAX_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    response = llm.invoke(messages)
    content = json.loads(response.content)

    return {
        **state,
        "wax": {
            **content,
        },
    }


def willingness_to_action_tool(state: State):
    """
    This tool is used to represent the final translation from willingness (WAX) into
    actual behavioral probability
    """

    print("WTX_AGENT called")

    input_data = f"""Here is the input data.
    willingness_level: {json.dumps(state['wax']['willingness_level'])}
    cqi: {state['context']['cqi']}
    blind_spot_index: {json.dumps(state['awx']['blind_spot_index'])}
    kernel_status: {state['meta']['kernel_status']}
    """
    messages = [
        SystemMessage(content=WTX_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(WTXState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "wtx": {
            **response,
        },
    }


def segment_tool(state: State):
    """
    This tool is used to classify actors or simulated profiles into behavioral segments based
    on their utility structure, awareness, willingness, behavioral probability,
    and contextual stability.
    """

    print("SEGMENT_AGENT called")

    input_data = f"""Here is the input data.
    inu: {state['inu']['inu']}
    knu: {state['knu']['knu']}
    idn: {state['idn']['identity_utility']}
    awareness_level: {state['awx']['awareness_level']}
    willingness_level: {state['wax']['willingness_level']}
    behavior_probability: {state['wtx']['behavior_probability']}
    cqi: {state['context']['cqi']}
    kernel_status: {state['meta']['kernel_status']}
    """
    messages = [
        SystemMessage(content=SEG_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    response = llm.invoke(messages)
    content = json.loads(response.content)
    return {
        **state,
        "seg": {
            **content,
        },
    }


def journey_tool(state: State):
    """
    This tool is used to provide structured transition probabilities and stage classifications
    """
    print("JNY_AGENT called")

    input_data = f"""Here is the input data.
    awareness_level: {state['awx']['awareness_level']}
    willingness_level: {state['wax']['willingness_level']}
    inu: {state['inu']['inu']}
    segment_confidence: 0.65 # TODO: need to get the segment confidence from the SEG_AGENT
    cqi: {state['context']['cqi']}
    kernel_status: {state['meta']['kernel_status']}
    """

    messages = [
        SystemMessage(content=JNY_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    response = llm.invoke(messages)
    content = json.loads(response.content)

    return {
        **state,
        "jny": {
            **content,
        },
    }


def intervention_tool(state: State):
    """
    This tool converts the behavioral journey outputs into structured intervention guidelines —
    showing what kind of action or measure is most effective to move the actor from
    the current to the next behavioral phase.
    """
    print("intervention_tool called")

    input_data = (
        f"Here is the input data.\n"
        f'intervention_type: "nudge",\n'
        f"fepsde_focus: {state["inu"]["fepsde"]},\n"
        f'journey_phase: "trigger",\n'
        f"context_vector: {json.dumps(state['context']['context_vector'])},\n"
        f"awareness_level: {state['awx']['awareness_level']},\n"
        f"willingness_level: {state['wax']['willingness_level']},\n"
        f"risk_factor: {state["wtx"]["risk_factor"]},\n"
        f"uncertainty_factor: {state["wtx"]["uncertainty_factor"]},\n"
    )

    messages = [
        SystemMessage(content=INT_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    response = llm.invoke(messages)
    content = json.loads(response.content)
    return {
        **state,
        "int": {
            **content,
        },
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
workflow.add_node("META_AGENT", meta_tool)
workflow.add_node("CONTEXT_AGENT", context_tool)
workflow.add_node("INU_AGENT", inu_tool)
workflow.add_node("KNU_AGENT", knu_tool)
workflow.add_node("IDN_AGENT", idn_tool)
workflow.add_node("AWX_AGENT", awareness_tool)
workflow.add_node("JNY_AGENT", journey_tool)
workflow.add_node("WAX_AGENT", willingness_tool)
workflow.add_node("WTX_AGENT", willingness_to_action_tool)
workflow.add_node("SEG_AGENT", segment_tool)
workflow.add_node("INT_AGENT", intervention_tool)
workflow.add_node("WATCHDOG_AGENT", watchdog_tool)

# Add edges to connect nodes
# KERNEL -> META -> CONTEXT -> INU -> KNU -> IDN -> AWX -> WAX -> SEG -> JNY -> INT -> WATCHDOG
workflow.add_edge(START, "KERNEL_AGENT")
# workflow.add_conditional_edges(
#     "KERNEL_AGENT",
#     meta_tool,
#     {"Fail": "WATCHDOG_AGENT", "Pass": "CONTEXT_AGENT"},
# )
workflow.add_edge("KERNEL_AGENT", "META_AGENT")
workflow.add_edge("META_AGENT", "CONTEXT_AGENT")

workflow.add_edge("CONTEXT_AGENT", "INU_AGENT")
workflow.add_edge("INU_AGENT", "KNU_AGENT")
workflow.add_edge("KNU_AGENT", "IDN_AGENT")
workflow.add_edge("IDN_AGENT", "AWX_AGENT")
workflow.add_edge("AWX_AGENT", "WAX_AGENT")
workflow.add_edge("WAX_AGENT", "WTX_AGENT")
workflow.add_edge("WTX_AGENT", "SEG_AGENT")
workflow.add_edge("SEG_AGENT", "JNY_AGENT")
workflow.add_edge("JNY_AGENT", "INT_AGENT")
workflow.add_edge("INT_AGENT", END)
# # TODO: add WTX_AGENT
# workflow.add_edge("WAX_AGENT", "SEG_AGENT")
# workflow.add_edge("JNY_AGENT", "INT_AGENT")
# workflow.add_edge("INT_AGENT", "WATCHDOG_AGENT")
# workflow.add_edge("WATCHDOG_AGENT", END)


# Compile
chain = workflow.compile()

# Generate and save PNG visualization
# png_bytes = chain.get_graph().draw_mermaid_png()
# with open("graph_visualization.png", "wb") as f:
#     f.write(png_bytes)
# print("Graph visualization saved to graph_visualization.png")

# Invoke
user_message = "As a budget-conscious college student who knows only a little about investment apps, I'd be willing to try one if it clearly saves me money and shows exactly how it works"
state = chain.invoke({"user_message": user_message})
print(state)

# agent = create_agent(
#     model="openai:gpt-5-mini",
#     tools=[chain.get_node("KERNEL_AGENT").tool],
#     system_prompt="You are a helpful assistant",
# )
# agent.invoke(
#     {"messages": [{"role": "user", "content": "What is the weather in San Francisco?"}]}
# )
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
