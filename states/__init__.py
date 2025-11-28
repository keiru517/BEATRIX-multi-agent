from typing_extensions import TypedDict

from states.kernel_state import KernelState
from states.meta_state import MetaState
from states.context_state import ContextState
from states.inu_state import INUState
from states.knu_state import KNUState
from states.idn_state import IDNState
from states.awx_state import AWXState
from states.wax_state import WAXState
from states.wtx_state import WTXState
from states.seg_state import SEGState
from states.jny_state import JNYState
from states.int_state import INTState
from states.watchdog_state import WatchdogState


class State(TypedDict):
    user_message: str
    total_nodes: int
    node_order: list[str]
    kernel: KernelState
    meta: MetaState
    context: ContextState
    inu: INUState
    knu: KNUState
    idn: IDNState
    awx: AWXState
    wax: WAXState
    wtx: WTXState
    seg: SEGState
    jny: JNYState
    int: INTState
    watchdog: WatchdogState
