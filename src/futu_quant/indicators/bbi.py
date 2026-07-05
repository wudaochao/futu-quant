import pandas as pd


def bbi(close: pd.Series, periods: tuple[int, int, int, int] = (3, 6, 12, 24)) -> pd.Series:
    """Calculate BBI from close prices."""
    averages = [close.rolling(period).mean() for period in periods]
    return sum(averages) / len(averages)
