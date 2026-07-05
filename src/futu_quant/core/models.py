from dataclasses import dataclass
from datetime import datetime

from futu_quant.core.enums import SignalSide, Timeframe


@dataclass(frozen=True)
class Bar:
    code: str
    timeframe: Timeframe
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    code: str
    side: SignalSide
    reason: str
    timestamp: datetime
    price: float
