from futu import *
import threading
import time
from datetime import datetime
import pytz

from multi_period_monitor import MultiPeriodIndicatorMonitor

trade_time_15m = {
    "09:30",
    "09:45",
    "10:00",
    "10:15",
    "10:30",
    "10:45",
    "11:00",
    "11:15",
    "11:30",
    "11:45",
    "12:00",
    "12:15",
    "12:30",
    "12:45",
    "13:00",
    "13:15",
    "13:30",
    "13:45",
    "14:15",
    "14:30",
    "14:45",
    "15:00",
    "15:15",
    "15:30",
    "15:45",
    "16:00",
}


code_list = ["US.QQQ", "US.TSLA"]
periods = [
    KLType.K_240M,
    KLType.K_WEEK,
    KLType.K_MON,
    KLType.K_QUARTER,
]

def get_us_eastern_now():
    return datetime.now(pytz.timezone("America/New_York"))

class RTDataHandler(RTDataHandlerBase):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(RTDataHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("RTData error, msg: %s" % data)
            return RET_ERROR, data

        code = data["code"][0]
        current_price = data["cur_price"][0]
        # print(data["time"][0], code, current_price)
        self.monitor.on_realtime_price(code, current_price)

        return RET_OK, data


class IndicatorCalcHandler(IndicatorCalcHandlerBase):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def on_recv_rsp(self, rsp_pb):
        ret_code, content = super(IndicatorCalcHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("indicator calc error:", content)
            return ret_code, content

        self.monitor.on_indicator_result(content)
        return RET_OK, content


def indicator_loop_thread(monitor):
    last_trigger_minute = None

    print("us indicator loop thread start")
    monitor.request_all_indicators()

    while True:
        current_minute = get_us_eastern_now().strftime("%H:%M")
        if current_minute in trade_time_15m and current_minute != last_trigger_minute:
            print(get_us_eastern_now().strftime("%Y-%m-%d %H:%M:%S"))
            last_trigger_minute = current_minute
            monitor.request_all_indicators()

        monitor.request_all_indicators()

        time.sleep(60)


def start_indicator_thread(monitor):
    thread = threading.Thread(target=indicator_loop_thread, args=(monitor,))
    thread.start()
    return thread


def us_start_indicator_thread():
    quote_ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
    monitor = MultiPeriodIndicatorMonitor(
        quote_ctx=quote_ctx,
        code_list=code_list,
        periods=periods,
    )

    quote_ctx.set_handler(IndicatorCalcHandler(monitor))
    quote_ctx.set_handler(RTDataHandler(monitor))

    ret, data = quote_ctx.subscribe(code_list, [SubType.RT_DATA], session=Session.ALL)
    if ret == RET_OK:
        print(data)
    else:
        print("subscribe error:", data)

    return start_indicator_thread(monitor)


if __name__ == "__main__":
    thread = us_start_indicator_thread()
    thread.join()
