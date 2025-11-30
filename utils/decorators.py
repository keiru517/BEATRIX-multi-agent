from datetime import datetime
from utils.logger import get_app_logger


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            get_app_logger(__name__).error(f"Error: {e}")
            return None

    return wrapper


def kernel_tool_decorator(func):
    def wrapper(*args, **kwargs):
        if not args:
            get_app_logger(__name__).warning(
                "Agent function called without expected positional arguments."
            )
        state = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            get_app_logger(__name__).error(f"Error: {e} in kernel_tool")
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
