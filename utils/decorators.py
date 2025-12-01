from datetime import datetime
from utils.logger import get_app_logger

logger = get_app_logger(__name__)


# deprecated
def agent_wrapper(func):
    def wrapper(*args, **kwargs):
        if not args:
            logger.warning(
                "Agent function called without expected positional arguments."
            )
        state = args[0]
        try:
            new_state = func(*args, **kwargs)
            next_index = state["next_agent_index"] + 1
            new_state["next_agent_index"] = next_index
            new_state["error"] = None
            print(f"new_state: {new_state}")
            return new_state
        except Exception as e:
            logger.error(f"Error: {e} in agent")
            new_state = {
                **state,
                "error": e,
            }
            return new_state

    return wrapper


# deprecated
def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    return wrapper


# deprecated
def kernel_tool_decorator(func):
    def wrapper(*args, **kwargs):
        if not args:
            logger.warning(
                "Agent function called without expected positional arguments."
            )
        state = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error: {e} in kernel_tool")
            return {
                **state,
                "kernel": {
                    "system_ready": False,
                    "agents_registered": [],
                    "version_info": "v1.1",  # TODO: need to get the version info from the kernel
                    "kernel_timestamp": datetime.now().isoformat(),
                },
            }

    return wrapper
