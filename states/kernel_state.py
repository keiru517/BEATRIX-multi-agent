from typing import TypedDict

########################################################
# Output (Kernel):
# •	system_status: initialized / failed
# •	agents_registered: list of all active agent IDs
# •	version_info: BCM version identifier (e.g., “v3.0”)
# •	kernel_timestamp: time of initialization
########################################################

class KernelState(TypedDict):
    system_ready: bool
    agents_registered: list[str]
    version_info: str
    kernel_timestamp: str