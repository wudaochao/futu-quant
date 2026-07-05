from futu_quant.core.enums import Market, StrategyHorizon
from futu_quant.strategies.timeframes import resolve_timeframes


DEFAULT_MARKETS = (Market.CN, Market.HK, Market.US)
DEFAULT_HORIZONS = (
    StrategyHorizon.SHORT,
    StrategyHorizon.MEDIUM,
    StrategyHorizon.LONG,
)


def describe_default_timeframes() -> dict[str, dict[str, tuple[str, str]]]:
    result: dict[str, dict[str, tuple[str, str]]] = {}
    for market in DEFAULT_MARKETS:
        result[market.value] = {}
        for horizon in DEFAULT_HORIZONS:
            timeframes = resolve_timeframes(market, horizon)
            result[market.value][horizon.value] = (
                timeframes.entry.value,
                timeframes.exit.value,
            )
    return result
