from typing import TypedDict


class ContextState(TypedDict):
    context_vector: ContextVector
    cqi: float
    context_state: str
    context_comment: str


class ContextVector(TypedDict):
    institutional: float
    social: float
    informational: float
    complexity: float
