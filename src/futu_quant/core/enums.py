from enum import Enum


class TextEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class Market(TextEnum):
    CN = "CN"
    HK = "HK"
    US = "US"


class Timeframe(TextEnum):
    M15 = "15m"
    H2 = "2h"
    H4 = "4h"
    WEEK = "1w"
    MONTH = "1M"


class StrategyHorizon(TextEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class SignalSide(TextEnum):
    WAIT = "wait"
    BUY = "buy"
    SELL = "sell"
