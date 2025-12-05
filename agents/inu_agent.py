import json
import os

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from llms import openai_llm
from states import State, INUState
from prompt import INU_AGENT_PROMPT
from utils.http_client import HTTPClient
from utils.logger import get_app_logger

load_dotenv()

logger = get_app_logger(__name__)


# deprecated
def inu_agent(state: State):
    """
    This tool is used to calculate individual utility of the user.
    """

    context_vector = state["context"]["context_vector"]
    axioms_list = []
    L_00 = next((x for x in state["axioms"] if x.get("execution_step") == "L-00"), None)
    axioms_list.append(L_00)
    for vector in context_vector.keys():
        logger.info(f"INU_AGENT context vector: {vector} = {context_vector[vector]}")
        # TODO: need to check the exact numbers and axiom id, just for flow
        if vector == "social" and context_vector[vector] > 0.5:
            axioms_list.append(
                next(
                    (x for x in state["axioms"] if x.get("execution_step") == "L-52"),
                    None,
                )
            )
        if vector == "risk" and context_vector[vector] > 0.4:
            axioms_list.append(
                next(
                    (x for x in state["axioms"] if x.get("execution_step") == "L-12"),
                    None,
                )
            )
        if vector == "stress" and context_vector[vector] > 0.6:
            axioms_list.append(
                next(
                    (x for x in state["axioms"] if x.get("execution_step") == "L-59"),
                    None,
                )
            )
        if vector == "complexity" and context_vector[vector] > 0.7:
            axioms_list.append(
                next(
                    (x for x in state["axioms"] if x.get("execution_step") == "L-61"),
                    None,
                )
            )
        if vector == "informational" and context_vector[vector] > 0.6:
            axioms_list.append(
                next(
                    (x for x in state["axioms"] if x.get("execution_step") == "L-11"),
                    None,
                )
            )
        if vector == "institutional" and context_vector[vector] > 0.8:
            axioms_list.append(
                next(
                    (x for x in state["axioms"] if x.get("execution_step") == "L-20"),
                    None,
                )
            )

    input_data = (
        f"Here is the context vector from KON: {json.dumps(state['context']['context_vector'])}"
        f" and CQI: {state['context']['cqi']}\n"
        f" and Axioms: {json.dumps(axioms_list)}"
    )
    logger.info(f"INU_AGENT input data: {input_data}")

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
