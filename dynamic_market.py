import threading
import time
from datetime import datetime

from futu import *

from multi_period_monitor import MultiPeriodIndicatorMonitor
from watchlist_config import describe_indicator_tasks, load_indicator_tasks


WATCHLIST_REFRESH_SECONDS = 60


class DynamicRTDataHandler(RTDataHandlerBase):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(DynamicRTDataHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("RTData error, msg: %s" % data)
            return RET_ERROR, data
        for _, row in data.iterrows():
            self.monitor.on_realtime_price(row["code"], row["cur_price"])
        return RET_OK, data


class DynamicIndicatorCalcHandler(IndicatorCalcHandlerBase):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def on_recv_rsp(self, rsp_pb):
        ret_code, content = super(DynamicIndicatorCalcHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("indicator calc error:", content)
            return ret_code, content
        self.monitor.on_indicator_result(content)
        return RET_OK, content


def _subscribe(quote_ctx, codes):
    if not codes:
        return
    print(codes)
    ret, data = quote_ctx.subscribe(
        sorted(codes), [SubType.RT_DATA], session=Session.ALL
    )
    if ret != RET_OK:
        print("subscribe error:", data)


def _unsubscribe(quote_ctx, codes):
    if not codes:
        return
    ret, data = quote_ctx.unsubscribe(sorted(codes), [SubType.RT_DATA])
    if ret != RET_OK:
        print("unsubscribe error:", data)


def start_dynamic_market(code_filter, label):
    quote_ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
    try:
        initial_tasks = load_indicator_tasks(quote_ctx, code_filter)
    except Exception as exc:
        print("%s watchlist initial load error: %s" % (label, exc))
        initial_tasks = {}

    monitor = MultiPeriodIndicatorMonitor(
        quote_ctx=quote_ctx,
        code_list=[],
        periods=[],
        indicator_tasks={},
    )
    monitor.update_indicator_tasks(initial_tasks)
    quote_ctx.set_handler(DynamicIndicatorCalcHandler(monitor))
    quote_ctx.set_handler(DynamicRTDataHandler(monitor))
    _subscribe(quote_ctx, initial_tasks)

    def run():
        print("%s dynamic indicator thread start" % label)
        monitor.request_all_indicators()
        now = datetime.now()
        last_indicator_slot = (
            now.year, now.month, now.day, now.hour, now.minute // 15
        )
        last_watchlist_refresh = time.monotonic()
        while True:
            now = datetime.now()
            slot = (now.year, now.month, now.day, now.hour, now.minute // 15)
            if slot != last_indicator_slot:
                last_indicator_slot = slot
                monitor.request_all_indicators()

            monotonic_now = time.monotonic()
            if monotonic_now - last_watchlist_refresh >= WATCHLIST_REFRESH_SECONDS:
                last_watchlist_refresh = monotonic_now
                try:
                    new_tasks = load_indicator_tasks(quote_ctx, code_filter)
                    added, removed, changed = monitor.update_indicator_tasks(new_tasks)
                    _unsubscribe(quote_ctx, removed)
                    _subscribe(quote_ctx, added)
                    if added or removed or changed:
                        print(
                            "%s watchlist updated: added=%s removed=%s changed=%s"
                            % (
                                label,
                                sorted(added),
                                sorted(removed),
                                sorted(changed),
                            )
                        )
                        for code in sorted(added):
                            print(
                                "%s new task: %s"
                                % (
                                    label,
                                    describe_indicator_tasks(
                                        code, new_tasks.get(code, set())
                                    ),
                                )
                            )
                        monitor.request_all_indicators()
                except Exception as exc:
                    print("%s watchlist refresh error: %s" % (label, exc))
            time.sleep(5)

    thread = threading.Thread(target=run, name="%s-monitor" % label)
    thread.start()
    return thread
