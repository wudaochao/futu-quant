from futu import *
import threading
import time
from datetime import datetime

from multi_period_monitor import MultiPeriodIndicatorMonitor
from dynamic_market import start_dynamic_market
from watchlist_config import is_a_share

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
    "09:26",
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

def analyze_policy(time_str, monitor):
    if time_str == "09:26":
        print("9:26")
    elif time_str == "11:25":
        print("11:25")
    elif time_str == "14:55":
        print("14:55")

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

        #if current_minute in trade_time_2h:
        #    analyze_policy(current_minute, monitor)


        time.sleep(5)

        # if current_minute in TRIGGER_MINUTES and current_minute != last_trigger_minute:
        #     print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #     last_trigger_minute = current_minute
        #     monitor.request_all_indicators()

# def start_indicator_thread(monitor):
#     thread = threading.Thread(target=indicator_loop_thread, args=(monitor,))
#     thread.start()
#     return thread

def start_indicator_thread():
    return start_dynamic_market(is_a_share, "A-share")
    # thread = start_indicator_thread(monitor)
    # thread.join()


if __name__ == "__main__":
    thread = start_indicator_thread()
    thread.join()
