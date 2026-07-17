# -*- coding: utf-8 -*-
"""
连接 Futu_OpenD，获取中芯国际最近 15 分钟 K 线，并计算最新 BBI 和 BOLL。

默认股票代码：HK.00981（中芯国际）
默认 Futu_OpenD：127.0.0.1:11111
"""
import argparse
import datetime as dt

import pandas as pd
from futu import *


BBI_PERIODS = (3, 6, 12, 24)
BOLL_PERIOD = 20
BOLL_STD_TIMES = 2


def get_recent_15m_kline(quote_ctx, code, lookback_days=10, max_count=300):
    """获取最近一段 15 分钟历史 K 线。"""
    end = dt.datetime.now().strftime("%Y-%m-%d")
    start = (dt.datetime.now() - dt.timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    ret, data, page_req_key = quote_ctx.request_history_kline(
        code=code,
        start=start,
        end=end,
        ktype=KLType.K_15M,
        autype=AuType.QFQ,
        fields=[KL_FIELD.ALL],
        max_count=max_count,
    )
    if ret != RET_OK:
        raise RuntimeError("request_history_kline failed: {}".format(data))

    if data.empty:
        raise RuntimeError("没有获取到 K 线数据，请确认 Futu_OpenD、行情权限和股票代码是否正常")

    return data


def add_bbi_and_boll(kline):
    """基于 close 价格计算 BBI 和 BOLL。"""
    df = kline.copy()
    df["time_key"] = pd.to_datetime(df["time_key"])
    df = df.sort_values("time_key").reset_index(drop=True)

    close = df["close"].astype(float)
    ma_values = [close.rolling(period).mean() for period in BBI_PERIODS]
    df["bbi"] = sum(ma_values) / len(ma_values)

    df["boll_mid"] = close.rolling(BOLL_PERIOD).mean()
    boll_std = close.rolling(BOLL_PERIOD).std(ddof=0)
    df["boll_upper"] = df["boll_mid"] + BOLL_STD_TIMES * boll_std
    df["boll_lower"] = df["boll_mid"] - BOLL_STD_TIMES * boll_std

    return df


def print_latest_indicator(df):
    indicator_cols = ["time_key", "code", "close", "bbi", "boll_mid", "boll_upper", "boll_lower"]
    valid_df = df.dropna(subset=["bbi", "boll_mid", "boll_upper", "boll_lower"])
    if valid_df.empty:
        raise RuntimeError("K 线数量不足，至少需要 {} 根 15 分钟 K 线".format(max(max(BBI_PERIODS), BOLL_PERIOD)))

    latest = valid_df.iloc[-1]
    print("最新 15 分钟 K 线指标：")
    for col in indicator_cols:
        value = latest[col]
        if isinstance(value, float):
            value = round(value, 4)
        print("{}: {}".format(col, value))


def main():
    parser = argparse.ArgumentParser(description="获取中芯国际 15 分钟 K 线并计算 BBI/BOLL")
    parser.add_argument("--host", default="127.0.0.1", help="Futu_OpenD 地址")
    parser.add_argument("--port", default=11111, type=int, help="Futu_OpenD 端口")
    parser.add_argument("--code", default="SH.688981", help="股票代码，默认 HK.00981")
    parser.add_argument("--lookback-days", default=10, type=int, help="向前获取多少个自然日的 K 线")
    parser.add_argument("--max-count", default=300, type=int, help="最多获取多少根 K 线")
    args = parser.parse_args()

    quote_ctx = OpenQuoteContext(host=args.host, port=args.port)
    try:
        kline = get_recent_15m_kline(
            quote_ctx=quote_ctx,
            code=args.code,
            lookback_days=args.lookback_days,
            max_count=args.max_count,
        )
        result = add_bbi_and_boll(kline)
        print_latest_indicator(result)
    finally:
        quote_ctx.close()


if __name__ == "__main__":
    main()
