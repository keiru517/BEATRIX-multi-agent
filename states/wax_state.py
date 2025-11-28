from typing import TypedDict


class WAXState(TypedDict):
    willingness_level: float
    inertia_index: float
    willingness_state: str
    willingness_comment: str
