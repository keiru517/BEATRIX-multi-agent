from typing import TypedDict

class KernelState(TypedDict):
    system_ready: bool
    agents_registered: list[str]
    version_info: str
    kernel_timestamp: str