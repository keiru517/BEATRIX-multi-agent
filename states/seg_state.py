from typing import TypedDict


class SEGState(TypedDict):
    segment_id: str
    segment_label: str
    segment_confidence: float
    dominant_utility: str
    segment_score: float
    mean_awareness: float
    mean_willingness: float
    mean_behavior_probability: float
    segment_comment: str
