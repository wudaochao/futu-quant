from dataclasses import dataclass
from typing import Optional

import pandas as pd

from futu_quant.core.enums import SignalSide
from futu_quant.core.models import Signal
from futu_quant.indicators.bbi import bbi
from futu_quant.indicators.boll import boll


@dataclass(frozen=True)
class BbiBollParams:
    bbi_periods: tuple[int, int, int, int] = (3, 6, 12, 24)
    boll_period: int = 20
    boll_width: float = 2.0
    use_low_touch: bool = True


class BbiBollStrategy:
    """Shared strategy template for short, medium, and long horizons."""

    def __init__(self, code: str, params: Optional[BbiBollParams] = None):
        self.code = code
        self.params = params or BbiBollParams()

    def generate_signal(
        self,
        entry_bars: pd.DataFrame,
        exit_bars: pd.DataFrame,
        has_position: bool,
    ) -> Signal:
        self._validate_bars(entry_bars, "entry_bars")
        self._validate_bars(exit_bars, "exit_bars")

        entry_latest = entry_bars.iloc[-1]
        exit_latest = exit_bars.iloc[-1]
        bands = boll(entry_bars["close"], self.params.boll_period, self.params.boll_width)
        exit_bbi = bbi(exit_bars["close"], self.params.bbi_periods)

        if has_position:
            latest_bbi = exit_bbi.iloc[-1]
            if pd.notna(latest_bbi) and exit_latest["close"] < latest_bbi:
                return Signal(
                    code=self.code,
                    side=SignalSide.SELL,
                    reason="exit close below higher-timeframe BBI",
                    timestamp=exit_latest.name,
                    price=float(exit_latest["close"]),
                )
            return self._wait(exit_latest, "holding position")

        latest_lower = bands.lower.iloc[-1]
        touch_price = entry_latest["low"] if self.params.use_low_touch else entry_latest["close"]
        if pd.notna(latest_lower) and touch_price <= latest_lower:
            return Signal(
                code=self.code,
                side=SignalSide.BUY,
                reason="entry price touched BOLL lower band",
                timestamp=entry_latest.name,
                price=float(entry_latest["close"]),
            )

        return self._wait(entry_latest, "no entry condition")

    def _wait(self, bar: pd.Series, reason: str) -> Signal:
        return Signal(
            code=self.code,
            side=SignalSide.WAIT,
            reason=reason,
            timestamp=bar.name,
            price=float(bar["close"]),
        )

    @staticmethod
    def _validate_bars(bars: pd.DataFrame, name: str) -> None:
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(bars.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {sorted(missing)}")
        if bars.empty:
            raise ValueError(f"{name} is empty")
