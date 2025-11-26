from typing_extensions import TypedDict

class State(TypedDict):
    user_message: str
    context: str
    utilities: UtilityState
    awareness: float
    journey: float
    willingness: float
    segment: float
    intervention: float
    validation: float
    total_nodes: int
    node_order: list[str]


class UtilityState(TypedDict):
    INU: INUState
    KNU: float
    IDN: float


class INUState(TypedDict):
    inu: float
    fepsde: FEPSDEState
    timing: TimingState
    explanation: str


class FEPSDEState(TypedDict):
    financial: float
    emotional: float
    physical: float
    social: float
    digital: float
    ecological: float


class TimingState(TypedDict):
    instant: float
    short: float
    medium: float
    long: float