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
from utils.decorators import error_handler, kernel_tool_decorator, agent_wrapper
from utils.logger import get_app_logger

from constants import START_NODE, END_NODE, AGENT_ORDER

# from agents import inu_agent
from llms import openai_llm
from utils.http_client import HTTPClient
from utils.axioms import load_axioms
from utils.github import read_github_json

# Load environment variables from .env file
# TODO: need to get from environment variables
load_dotenv()

logger = get_app_logger(__name__)

http_client = HTTPClient(
    base_url=os.getenv("BEATRIX_API_URL"),
    timeout=10,
    auth_token=os.getenv("BEATRIX_API_KEY"),
)


TOTAL_NODES = len(AGENT_ORDER)


def _load_module_data():
    OWNER = "FehrAdvice-Partners-AG"
    REPO = "beatrix-api"
    BRANCH = "feat/schema"
    TOKEN = os.getenv("GITHUB_TOKEN")
    MODULE_PATHS = [
        "awx/awx.json",
        "context/context.json",
        "idn/idn.json",
        "int/int.json",
        "inu/inu.json",
        "jny/jny.json",
        "knu/knu.json",
        "meta/meta.json",
        "seg/seg.json",
        "wax/wax.json",
        "wtx/wtx.json",
    ]
    modules = {}
    for path in MODULE_PATHS:
        data = read_github_json(OWNER, REPO, BRANCH, path, TOKEN)
        if data:
            modules[path.split("/")[0].upper()] = data
        else:
            logger.error(f"Failed to read module data from {path}")
            return None
    return modules


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

    # TODO: need to get the chapter content id from the kernel
    modules = _load_module_data()
    if modules is None:
        logger.error("kernel_tool: failed to load module data")
        return {
            **state,
            "next_agent_index": 1,
            "error": "Failed to load module data",
        }

    # Get the total number of nodes
    total_nodes = len(workflow.nodes)
    agent_registered = list(workflow.nodes.keys())

    # TODO: need to do the validation of all the nodes as well

    if total_nodes == TOTAL_NODES and agent_registered == AGENT_ORDER:
        logger.info("kernel_tool: all modules are here and in the right order")
        return {
            **state,
            "modules": modules,
            "next_agent_index": 1,
            "kernel": {
                "system_ready": True,
                "agents_registered": agent_registered,
                "version_info": "v1.0",  # TODO: need to get the version info from the kernel
                "kernel_timestamp": datetime.now().isoformat(),
            },
        }
    else:
        logger.error("kernel_tool: all modules are not here or in the right order")
        return {
            **state,
            "modules": modules,
            "next_agent_index": 1,
            "kernel": {
                "system_ready": False,
                "agents_registered": agent_registered,
                "version_info": "v1.0",  # TODO: need to get the version info from the kernel
                "kernel_timestamp": datetime.now().isoformat(),
            },
        }


def meta_tool(state: State):
    """Gate function to check if the initialization is successful."""

    axioms = state.get("axioms", None)
    # TODO: need to use a variable for axiom length
    if axioms is None or len(axioms) < 10:
        return {
            **state,
            "kernel": {
                **state["kernel"],
                "system_ready": False,
            },
            "error": "Incomplete axiom set",
            "meta_status": "REINIT_REQUIRED",
        }
    else:
        input_data = (
            f"Here is the input data.\n"
            f"Kernel status: {state['kernel']['system_ready']}\n"
            f"Agents registered: {', '.join(state['kernel']['agents_registered'])}\n"
            f"Version info: {state['kernel']['version_info']}\n"
            f"Kernel timestamp: {state['kernel']['kernel_timestamp']}"
        )

        structured_llm = openai_llm.with_structured_output(MetaState)
        response = structured_llm.invoke(
            [
                SystemMessage(content=META_AGENT_PROMPT),
                HumanMessage(content=input_data),
            ]
        )

        return {
            **state,
            "kernel": {
                **state["kernel"],
                "system_ready": True,
            },
            "error": None,
            "meta_status": "OK",
            "next_agent_index": 2,
            "meta": {
                **response,
            },
        }


# TODO: need to integrate API
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

    structured_llm = openai_llm.with_structured_output(ContextState)
    response = structured_llm.invoke(
        [
            SystemMessage(content=CONTEXT_AGENT_PROMPT),
            HumanMessage(content=input_data),
        ]
    )

    return {
        **state,
        "next_agent_index": 3,
        "context": {
            **response,
        },
    }


def inu_agent(state: State):
    """
    This tool is used to calculate individual utility of the user.
    """

    # TODO: need to use correct threshold
    AXIOM_CONFIG = {
        "social": {"threshold": 0.5, "axiom_id": "L-52"},
        "risk": {"threshold": 0.4, "axiom_id": "L-12"},
        "stress": {"threshold": 0.6, "axiom_id": "L-59"},
        "complexity": {"threshold": 0.7, "axiom_id": "L-61"},
        "informational": {"threshold": 0.6, "axiom_id": "L-11"},
        "institutional": {"threshold": 0.8, "axiom_id": "L-20"},
    }
    axiom_map = {
        x.get("execution_step"): x
        for x in state.get("axioms", [])
        if x and x.get("execution_step")  # Ensure it's not None and has the key
    }

    context_vector = state["context"]["context_vector"]
    axioms_list = []
    L_00 = next((x for x in state["axioms"] if x.get("execution_step") == "L-00"), None)
    axioms_list.append(L_00)

    for vector, value in context_vector.items():
        config = AXIOM_CONFIG.get(vector)
        if config and value > config["threshold"]:
            axiom_id = config["axiom_id"]
            axiom = axiom_map.get(axiom_id)
            if axiom:
                axioms_list.append(axiom)

    input_data = (
        f"Here is the context vector from KON: {context_vector}"
        f" and CQI: {state['context']['cqi']}"
        # f" and Axioms: {json.dumps(axioms_list)}"
    )

    messages = [
        SystemMessage(content=INU_AGENT_PROMPT),
        HumanMessage(content=input_data),
    ]
    structured_llm = openai_llm.with_structured_output(INUState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 4,
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
    structured_llm = openai_llm.with_structured_output(KNUState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 5,
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
    structured_llm = openai_llm.with_structured_output(IDNState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 6,
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
    structured_llm = openai_llm.with_structured_output(AWXState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 7,
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
    structured_llm = openai_llm.with_structured_output(WAXState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 8,
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
    structured_llm = openai_llm.with_structured_output(WTXState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 9,
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
    structured_llm = openai_llm.with_structured_output(SEGState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 10,
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
    structured_llm = openai_llm.with_structured_output(JNYState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 11,
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
    structured_llm = openai_llm.with_structured_output(INTState)
    response = structured_llm.invoke(messages)

    return {
        **state,
        "next_agent_index": 12,
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
    global error
    if error is not None:
        return {
            **state,
            "next_agent_index": 1,
            "error": error,
        }
    else:
        return {
            **state,
            "next_agent_index": 1,
            "error": None,
        }
    # TODO: need to implement the watchdog logic
    return {
        **state,
        "validation": "VALIDATION DATA",
    }


# global error
# error = None
error = None


def check_agent_prerequisites(next_agent_name: str, state: State) -> bool:
    """Checks if the state meets the required prerequisites for the given agent."""

    # Use .get() defensively to avoid KeyError on missing top-level or nested keys

    if next_agent_name == "CONTEXT_AGENT":

        # cqi should be between 0.45 and 0.65 from META_AGENT
        current_cqi = float(state.get("meta", {}).get("current_cqi"))
        if current_cqi < 0.45 or current_cqi > 0.65:
            logger.info(
                "Validation Failed for CONTEXT_AGENT: because current cqi is not between 0.45 and 0.65."
            )
            global error
            error = "Validation Failed for CONTEXT_AGENT: because current cqi is not between 0.45 and 0.65."
            # TODO: need to change into False later
            return True

    elif next_agent_name == "INU_AGENT":
        context_state = state.get("context", {}).get("context_state")
        # Check for existence and then check the internal state/activity
        if not context_state or context_state != "active":
            logger.info(
                "Validation Failed for INU_AGENT: because context state of CONTEXT_AGENT is not active."
            )
            error = "Validation Failed for INU_AGENT: because context state of CONTEXT_AGENT is not active."

            return False

    elif next_agent_name == "IDN_AGENT":
        # "integrity_flag" from KNU_AGENT should be "ok"
        knu_integrity_flag = state.get("knu", {}).get("integrity_flag")
        if knu_integrity_flag != "ok":
            logger.info(
                "Validation Failed for IDN_AGENT: because KNU integrity flag is not ok."
            )
            # global error
            error = (
                "Validation Failed for IDN_AGENT: because KNU integrity flag is not ok."
            )
            return False
    return True


def route_agents(state: State):
    """Decides the next step: Error Handler, Next Agent, or END."""

    if state["kernel"]["system_ready"] is False:
        return "error"

    next_agent_index = state["next_agent_index"]
    if next_agent_index >= len(AGENT_ORDER):
        return END

    next_agent_name = AGENT_ORDER[next_agent_index]

    if not check_agent_prerequisites(next_agent_name, state):
        return "error"

    return next_agent_name


# Build workflow
workflow = StateGraph(State)


# Add nodes
workflow.add_node("KERNEL_AGENT", lambda state: kernel_tool(state, workflow))
workflow.add_node("META_AGENT", meta_tool)
workflow.add_node("CONTEXT_AGENT", context_tool)
workflow.add_node("INU_AGENT", inu_agent)
workflow.add_node("KNU_AGENT", knu_tool)
workflow.add_node("IDN_AGENT", idn_tool)
workflow.add_node("AWX_AGENT", awareness_tool)
workflow.add_node("WAX_AGENT", willingness_tool)
workflow.add_node("WTX_AGENT", willingness_to_action_tool)
workflow.add_node("SEG_AGENT", segment_tool)
workflow.add_node("JNY_AGENT", journey_tool)
workflow.add_node("INT_AGENT", intervention_tool)
workflow.add_node("WATCHDOG_AGENT", watchdog_tool)

# Add edges to connect nodes
# KERNEL -> META -> CONTEXT -> INU -> KNU -> IDN -> AWX -> WAX -> SEG -> JNY -> INT -> WATCHDOG
workflow.add_edge(START, "KERNEL_AGENT")
for node_name in AGENT_ORDER:
    current_node_index = AGENT_ORDER.index(node_name)
    next_node_index = current_node_index + 1
    if next_node_index >= len(AGENT_ORDER):
        break
    workflow.add_conditional_edges(
        node_name,
        route_agents,
        {
            "error": "WATCHDOG_AGENT",
            "END": END,
            AGENT_ORDER[next_node_index]: AGENT_ORDER[next_node_index],
        },
    )

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
