from typing_extensions import TypedDict


class MetaState(TypedDict):
    meta_axiom_version: str
    kernel_status: str
    active_modules: list[str]
    coherence_range: str
    current_cqi: str
    integrity_flag: str
    time_context: str
    meta_comment: str
