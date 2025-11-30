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
from states import (
    State,
    KernelState,
    MetaState,
    ContextState,
    INUState,
    KNUState,
    IDNState,
    AWXState,
    WAXState,
    WTXState,
    SEGState,
    JNYState,
    INTState,
    WatchdogState,
)
from utils.decorators import error_handler, kernel_tool_decorator
from utils.logger import get_app_logger


# Load environment variables from .env file
# TODO: need to get from environment variables
load_dotenv()

logger = get_app_logger(__name__)

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
    "WAX_AGENT",
    "WTX_AGENT",
    "SEG_AGENT",
    "JNY_AGENT",
    "INT_AGENT",
    # "WATCHDOG_AGENT",
]

TOTAL_NODES = len(AGENT_ORDER) + 1  # +1 for KERNEL_AGENT


# Nodes
@kernel_tool_decorator
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
    logger.info(
        f"kernel_tool: total_nodes: {total_nodes}, TOTAL_NODES: {TOTAL_NODES}, order: {order}, AGENT_ORDER: {AGENT_ORDER}"
    )
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

    input_data = (
        f"kernel_status: {state['meta']['kernel_status']}\n"
        f"user_message: {state['user_message']}\n"
        "environment: {{\n"
        '    "institutional": 0.82,\n'
        '    "social": 0.58,\n'
        '    "informational": "medium",\n'
        '    "complexity": "very high",\n'
        "}}\n"
    )

    structured_llm = llm.with_structured_output(ContextState)
    response = structured_llm.invoke(
        [
            SystemMessage(content=CONTEXT_AGENT_PROMPT),
            HumanMessage(content=input_data),
        ]
    )

    return {
        **state,
        "context": {
            **response,
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

    input_data = f"Here is the INU data, KNU data and KON data: {json.dumps(state['inu'])} and {json.dumps(state['knu'])} and {json.dumps(state['context'])}"
    messages = [
        SystemMessage(content=IDN_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(IDNState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "idn": {
            **response,
        },
    }


def awareness_tool(state: State):
    """
    This tool is used to estimate the level of awareness based on individual utility
    (INU), collective alignment (KNU), and contextual stability (CQI).
    """

    input_data = (
        f"Here is the input data.\n"
        f"inu: {state['inu']['inu']}\n"
        f"alignment_index: {state['knu']['alignment_index']}\n"
        f"cqi: {state['context']['cqi']}\n"
        f"kernel_status: {state['meta']['kernel_status']}\n"
    )
    messages = [
        SystemMessage(content=AWX_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(AWXState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "awx": {
            **response,
        },
    }


def willingness_tool(state: State):
    """
    This tool is used to estimate an actor's readiness to act upon their awareness.
    """

    input_data = (
        f"Here is the input data.\n"
        f"awareness_level: {state['awx']['awareness_level']}\n"
        f"inu: {state['inu']['inu']}\n"
        f"cqi: {state['context']['cqi']}\n"
        f"kernel_status: {state['meta']['kernel_status']}\n"
    )
    messages = [
        SystemMessage(content=WAX_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(WAXState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "wax": {
            **response,
        },
    }


def willingness_to_action_tool(state: State):
    """
    This tool is used to represent the final translation from willingness (WAX) into
    actual behavioral probability
    """

    input_data = (
        f"Here is the input data.\n"
        f"willingness_level: {state['wax']['willingness_level']}\n"
        f"cqi: {state['context']['cqi']}\n"
        f"blind_spot_index: {state['awx']['blind_spot_index']}\n"
        f"kernel_status: {state['meta']['kernel_status']}\n"
    )
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

    input_data = (
        f"Here is the input data.\n"
        f"inu: {state['inu']['inu']}\n"
        f"knu: {state['knu']['knu']}\n"
        f"idn: {state['idn']['identity_utility']}\n"
        f"awareness_level: {state['awx']['awareness_level']}\n"
        f"willingness_level: {state['wax']['willingness_level']}\n"
        f"behavior_probability: {state['wtx']['behavior_probability']}\n"
        f"cqi: {state['context']['cqi']}\n"
        f"kernel_status: {state['meta']['kernel_status']}\n"
    )
    messages = [
        SystemMessage(content=SEG_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(SEGState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "seg": {
            **response,
        },
    }


def journey_tool(state: State):
    """
    This tool is used to provide structured transition probabilities and stage classifications
    """

    input_data = (
        f"Here is the input data.\n"
        f"awareness_level: {state['awx']['awareness_level']}\n"
        f"willingness_level: {state['wax']['willingness_level']}\n"
        f"inu: {state['inu']['inu']}\n"
        f"segment_confidence: 0.65 # TODO: need to get the segment confidence from the SEG_AGENT\n"
        f"cqi: {state['context']['cqi']}\n"
        f"kernel_status: {state['meta']['kernel_status']}\n"
    )
    messages = [
        SystemMessage(content=JNY_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(JNYState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "jny": {
            **response,
        },
    }


def intervention_tool(state: State):
    """
    This tool converts the behavioral journey outputs into structured intervention guidelines —
    showing what kind of action or measure is most effective to move the actor from
    the current to the next behavioral phase.
    """

    input_data = (
        f"Here is the input data.\n"
        f"journey_stage: {state['jny']['journey_stage']}\n"
        f"transition_probability: {state['jny']['transition_probability']}\n"
        f"drift_index: {state['jny']['drift_index']}\n"
        f"journey_state: {state['jny']['journey_state']}\n"
        f"journey_comment: {state['jny']['journey_comment']}\n"
    )
    messages = [
        SystemMessage(content=INT_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = llm.with_structured_output(INTState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "int": {
            **response,
        },
    }


def watchdog_tool(state: State):
    """
    1. Logs and classifies the anomaly from state['error'].
    2. Decides the next action: 'REINIT' (Kernel) or 'ALERT' (Meta).
    """

    # response = llm.invoke(f"Validate the following intervention: {state['intervention']}")

    # TODO: need to implement the watchdog logic
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
# workflow.add_node("WATCHDOG_AGENT", watchdog_tool)

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
