import pandas as pd

from futu_quant.indicators.bbi import bbi
from futu_quant.indicators.boll import boll


def test_bbi_has_expected_value_after_all_windows_ready():
    close = pd.Series(range(1, 25), dtype=float)
    result = bbi(close)
    expected = (
        close.rolling(3).mean().iloc[-1]
        + close.rolling(6).mean().iloc[-1]
        + close.rolling(12).mean().iloc[-1]
        + close.rolling(24).mean().iloc[-1]
    ) / 4
    assert result.iloc[-1] == expected


def test_boll_returns_three_bands():
    close = pd.Series(range(1, 31), dtype=float)
    bands = boll(close)
    assert bands.upper.iloc[-1] > bands.mid.iloc[-1]
    assert bands.lower.iloc[-1] < bands.mid.iloc[-1]
