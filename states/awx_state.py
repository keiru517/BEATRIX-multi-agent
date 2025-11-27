from typing import TypedDict


class AWXState(TypedDict):
    awareness_index: float
    awareness_state: str
    key_drivers: list[str]
    comment: str
