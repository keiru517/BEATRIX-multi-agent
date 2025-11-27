from typing import TypedDict


class WatchdogState(TypedDict):
    system_status: str
    alert_level: str
    affected_module: str
    summary_report: str
    log_entry: str
