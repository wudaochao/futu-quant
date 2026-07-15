from futu import *
import threading
import time
from datetime import datetime

from multi_period_monitor import MultiPeriodIndicatorMonitor

TRIGGER_MINUTES = {0, 15, 30, 45}

code_list = ["SH.688981", "SH.000001"]
periods = [
    KLType.K_15M,
    KLType.K_120M,
    KLType.K_WEEK,
    KLType.K_MON,
    KLType.K_QUARTER,
]

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
    "13:00",
    "13:15",
    "13:30",
    "13:45",
    "14:15",
    "14:30",
    "14:45",
    "15:00",
}

trade_time_2h = {
    "11:25",
    "14:55"
}

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
        #print(data["time"][0], code, current_price)
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

    print("indicator loop thread start")
    monitor.request_all_indicators()

    while True:
        current_minute = datetime.now().strftime("%H:%M")
        if current_minute in trade_time_15m and current_minute != last_trigger_minute:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            last_trigger_minute = current_minute
            monitor.request_all_indicators()

        time.sleep(5)

        # if current_minute in TRIGGER_MINUTES and current_minute != last_trigger_minute:
        #     print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #     last_trigger_minute = current_minute
        #     monitor.request_all_indicators()

def start_indicator_thread(monitor):
    thread = threading.Thread(target=indicator_loop_thread, args=(monitor,))
    thread.start()
    return thread


if __name__ == "__main__":
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

    thread = start_indicator_thread(monitor)
    thread.join()
