from typing import TypedDict


class KNUState(TypedDict):
    knu: float
    legit: float
    normCoh: float
    alignment_index: float
    collective_comment: str
    integrity_flag: str
