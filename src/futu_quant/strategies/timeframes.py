from dataclasses import dataclass

from futu_quant.core.enums import Market, StrategyHorizon, Timeframe


@dataclass(frozen=True)
class StrategyTimeframes:
    entry: Timeframe
    exit: Timeframe


def resolve_timeframes(market: Market, horizon: StrategyHorizon) -> StrategyTimeframes:
    intraday_exit = Timeframe.H2 if market == Market.CN else Timeframe.H4

    if horizon == StrategyHorizon.SHORT:
        return StrategyTimeframes(entry=Timeframe.M15, exit=intraday_exit)

    if horizon == StrategyHorizon.MEDIUM:
        return StrategyTimeframes(entry=intraday_exit, exit=Timeframe.WEEK)

    if horizon == StrategyHorizon.LONG:
        return StrategyTimeframes(entry=Timeframe.WEEK, exit=Timeframe.MONTH)

    raise ValueError(f"unsupported strategy horizon: {horizon}")
