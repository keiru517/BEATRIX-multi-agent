from typing import TypedDict

class JNYState(TypedDict):
    current_phase: str
    next_phase: str
    journey_vector: list[str]
    key_enablers: list[str]
    key_barriers: list[str]
    comment: str