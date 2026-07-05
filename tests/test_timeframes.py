from futu_quant.core.enums import Market, StrategyHorizon, Timeframe
from futu_quant.strategies.timeframes import resolve_timeframes


def test_cn_short_uses_2h_exit():
    timeframes = resolve_timeframes(Market.CN, StrategyHorizon.SHORT)
    assert timeframes.entry == Timeframe.M15
    assert timeframes.exit == Timeframe.H2


def test_hk_short_uses_4h_exit():
    timeframes = resolve_timeframes(Market.HK, StrategyHorizon.SHORT)
    assert timeframes.entry == Timeframe.M15
    assert timeframes.exit == Timeframe.H4


def test_us_medium_uses_4h_entry_and_week_exit():
    timeframes = resolve_timeframes(Market.US, StrategyHorizon.MEDIUM)
    assert timeframes.entry == Timeframe.H4
    assert timeframes.exit == Timeframe.WEEK
