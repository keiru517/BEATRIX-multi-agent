from typing import TypedDict


class JNYState(TypedDict):
    journey_stage: str
    transition_probability: float
    drift_index: float
    journey_state: str
    journey_comment: str
