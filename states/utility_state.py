from typing_extensions import TypedDict

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