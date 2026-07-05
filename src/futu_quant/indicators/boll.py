from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BollBands:
    upper: pd.Series
    mid: pd.Series
    lower: pd.Series


def boll(close: pd.Series, period: int = 20, width: float = 2.0) -> BollBands:
    """Calculate BOLL bands from close prices."""
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    return BollBands(
        upper=mid + width * std,
        mid=mid,
        lower=mid - width * std,
    )
