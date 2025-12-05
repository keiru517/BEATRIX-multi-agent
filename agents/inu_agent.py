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


def inu_agent(state: State):
    """
    This tool is used to calculate individual utility of the user.
    """

    # TODO: if context_state != active, do not calculation
    # TODO: if cqi < 0.3, trigger WATCHDOG_AGENT

    input_data = (
        f"Here is the context vector from KON: {json.dumps(state['context']['context_vector'])}"
        f" and CQI: {state['context']['cqi']}"
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
