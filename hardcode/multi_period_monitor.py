import json
from datetime import datetime, timedelta
from urllib import request
from urllib.error import HTTPError, URLError

from futu import *


DEFAULT_FEISHU_WEBHOOK_URL = (
    "https://open.feishu.cn/open-apis/bot/v2/hook/"
    "0f2015b5-6d16-4f3b-b8c6-e0df7853db37"
)


class MultiPeriodIndicatorMonitor:
    def __init__(
        self,
        quote_ctx,
        code_list,
        periods,
        target_kline_count=30,
        feishu_webhook_url=DEFAULT_FEISHU_WEBHOOK_URL,
        suppress_feishu_in_same_period=True,
    ):
        self.quote_ctx = quote_ctx
        self.code_list = code_list
        self.periods = periods
        self.target_kline_count = target_kline_count
        self.feishu_webhook_url = feishu_webhook_url
        self.suppress_feishu_in_same_period = suppress_feishu_in_same_period

        self.indicator_map = self._init_indicator_map()
        self.last_indicator_map = self._init_indicator_map()
        self.close_price_map = self._init_close_price_map()
        self.last_price_map = {code: 0.0 for code in code_list}
        self.calc_boll_map = {}
        self.calc_bbi_map = {}
        self.sent_feishu_period_keys = set()

    def _init_indicator_map(self):
        return {
            period: {
                code: {
                    "BBI": None,
                    "BOLL": {},
                }
                for code in self.code_list
            }
            for period in self.periods
        }

    def _init_close_price_map(self):
        return {
            period: {
                code: {
                    "CLOSE": 0.0,
                }
                for code in self.code_list
            }
            for period in self.periods
        }

    def request_all_indicators(self):
        for period in self.periods:
            for code in self.code_list:
                self.request_indicator(code, period)

    def request_indicator(self, code, period):
        start, end = self.get_kline_date_range(period)
        ret, kl_data, _ = self.quote_ctx.request_history_kline(
            code,
            start=start,
            end=end,
            ktype=period,
        )
        if ret != RET_OK:
            print(
                f"request_history_kline error: code={code}, "
                f"period={self.period_name(period)}, msg={kl_data}"
            )
            return
        else:
            self.close_price_map[period][code] = kl_data["close"].tolist()[-1]

        if not self.has_enough_kline(kl_data, code, period):
            return

        ret, calc_id = self.quote_ctx.request_indicator_calc_async(
            "BOLL",
            IndicatorLangType.MYLANG,
            code,
            period,
            kl_data,
        )
        if ret == RET_OK:
            self.calc_boll_map[calc_id] = (code, period)
        else:
            print(
                f"BOLL calc error: code={code}, "
                f"period={self.period_name(period)}, msg={calc_id}"
            )

        ret, calc_id = self.quote_ctx.request_indicator_calc_async(
            "BBI",
            IndicatorLangType.MYLANG,
            code,
            period,
            kl_data,
        )
        if ret == RET_OK:
            self.calc_bbi_map[calc_id] = (code, period)
        else:
            print(
                f"BBI calc error: code={code}, "
                f"period={self.period_name(period)}, msg={calc_id}"
            )

    def get_kline_date_range(self, period):
        end_date = datetime.now().date()
        lookback_days_map = {
            KLType.K_15M: 10,
            KLType.K_120M: 45,
            KLType.K_240M: 90,
            KLType.K_WEEK: 260,
            KLType.K_MON: 1100,
            KLType.K_QUARTER: 3000,
        }
        lookback_days = lookback_days_map.get(period, 260)
        start_date = end_date - timedelta(days=lookback_days)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def has_enough_kline(self, kl_data, code, period):
        count = len(kl_data)
        minimum_count = 25
        # if count < self.target_kline_count:
        #     print(
        #         f"kline count less than target: code={code}, "
        #         f"period={self.period_name(period)}, count={count}, "
        #         f"target={self.target_kline_count}"
        #     )
        if count < minimum_count:
            print(
                f"skip indicator calc, kline count too small: code={code}, "
                f"period={self.period_name(period)}, count={count}, "
                f"minimum={minimum_count}"
            )
            return False
        return True

    def on_indicator_result(self, content):
        calc_id = content["calc_id"]
        output_rows = content["output_rows"]
        if len(output_rows) < 2:
            print(f"indicator output rows too short: calc_id={calc_id}")
            return

        latest = output_rows[-2]
        newest = output_rows[-1]

        if calc_id in self.calc_boll_map:
            code, period = self.calc_boll_map.pop(calc_id)
            mid = 2 * newest["values"][0] - latest["values"][0]
            upper = 2 * newest["values"][1] - latest["values"][1]
            lower = 2 * newest["values"][2] - latest["values"][2]
            self.indicator_map[period][code]["BOLL"] = {
                "MID": mid,
                "UPPER": upper,
                "LOWER": lower,
            }
            self.last_indicator_map[period][code]["BOLL"] = {
                "MID": newest["values"][0],
                "UPPER": newest["values"][1],
                "LOWER": newest["values"][2],
            }

            #self.print_indicator_update(code, period)
            #return

        if calc_id in self.calc_bbi_map:
            code, period = self.calc_bbi_map.pop(calc_id)
            bbi = 2 * newest["values"][0] - latest["values"][0]
            self.indicator_map[period][code]["BBI"] = bbi
            self.last_indicator_map[period][code]["BBI"] = newest["values"][0]


        #self.print_indicator_update(code, period)
        return

    def print_indicator_update(self, code, period):
        indicators = self.indicator_map[period][code]
        print(
            f"indicator updated: code={code}, "
            f"period={self.period_name(period)}, value={indicators}"
        )

    def on_realtime_price(self, code, current_price):
        if code not in self.last_price_map:
            return

        last_price = self.last_price_map[code]
        if last_price == 0.0:
            self.last_price_map[code] = current_price
            return

        for period in self.periods:
            self.check_period_alert(code, period, last_price, current_price)

        self.last_price_map[code] = current_price

    def check_period_alert(self, code, period, last_price, current_price):
        last_close = self.close_price_map[period][code]
        indicators = self.indicator_map[period][code]
        last_indicators = self.last_indicator_map[period][code]
        bbi = indicators["BBI"]
        last_bbi = last_indicators["BBI"]
        boll = indicators["BOLL"]
        last_boll = last_indicators["BOLL"]
        if bbi is None or not boll or not last_boll:
            return

        mid = boll.get("MID")
        upper = boll.get("UPPER")
        lower = boll.get("LOWER")

        last_mid = last_boll.get("MID")
        last_upper = last_boll.get("UPPER")
        last_lower = last_boll.get("LOWER")

        if mid is None or upper is None or lower is None:
            return

        if last_mid is None or last_upper is None or last_lower is None:
            return

        period_name = self.period_name(period)
        #print(f"{code} {period_name}: bbi={bbi} mid={mid}, upper={upper}, lower={lower} last_close={last_close}, last_price={last_price} current={current_price}")
        #print(f"{code} {period_name}: last_bbi={last_bbi} last_mid={last_mid}, last_upper={last_upper}, last_lower={last_lower}")

        #self.check_cross(code, period, period_name, "BBI", bbi, last_price, current_price)
        #self.check_cross(code, period, period_name, "BOLL中轨", mid, last_price, current_price)
        #self.check_cross(code, period, period_name, "BOLL上轨", upper, last_price, current_price)
        #self.check_cross(code, period, period_name, "BOLL下轨", lower, last_price, current_price)
        if last_close > last_bbi > last_mid:
            if current_price <= bbi < last_price:
                action = f"{code}跌到{period_name}BBI"
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {action}: bbi={bbi:.2f}, last_price={last_price:.2f} current={current_price:.2f}"
                #print(message)
                self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, action))
        elif last_close < last_bbi < last_mid:
            if current_price >= bbi > last_price:
                action = f"{code}涨到{period_name}BBI"
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {action}: bbi={bbi:.2f}, last_price={last_price:.2f} current={current_price:.2f}"
                #print(message)
                self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, action))

        if last_mid < last_close < last_upper:
            if current_price >= upper > last_price:
                action = f"{code}涨到{period_name}BOLL上轨"
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {action}: upper={upper:.2f}, last_price={last_price:.2f} current={current_price:.2f}"
                #print(message)
                self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, action))
            elif current_price < mid < last_price:
                action = f"{code}跌到{period_name}BOLL中轨"
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {action}: mid={mid:.2f}, last_price={last_price:.2f} current={current_price:.2f}"
                #print(message)
                self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, action))
        elif last_mid > last_close > last_lower:
            if current_price >= mid > last_price:
                action = f"{code}涨到{period_name}BOLL中轨"
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {action}: mid={mid:.2f}, last_price={last_price:.2f} current={current_price:.2f}"
                #print(message)
                self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, action))
            elif current_price <= lower < last_price:
                action = f"{code}跌到{period_name}BOLL下轨"
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {action}: lower={lower:.2f}, last_price={last_price:.2f} current={current_price:.2f}"
                #print(message)
                self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, action))

    def check_cross(self, code, period, period_name, indicator_name, line_value, last_price, current_price):
        if last_price < line_value <= current_price:
            message = (
                f"{code} 上穿{period_name}{indicator_name}: "
                f"line={line_value}, last={last_price}, current={current_price}"
            )
            print(message)
            self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, "up"))
        elif last_price > line_value >= current_price:
            message = (
                f"{code} 下穿{period_name}{indicator_name}: "
                f"line={line_value}, last={last_price}, current={current_price}"
            )
            print(message)
            self.send_feishu_message(message, suppress_key=self.get_feishu_suppress_key(code, "down"))

    def send_feishu_message(self, text, suppress_key=None):
        if not self.feishu_webhook_url:
            return

        if self.should_suppress_feishu(suppress_key):
            return

        print(text)
        payload = {
            "msg_type": "text",
            "content": {
                "text": text,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.feishu_webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=5) as resp:
                if resp.status >= 300:
                    print(f"feishu webhook error: status={resp.status}")
        except HTTPError as exc:
            print(f"feishu webhook http error: status={exc.code}, msg={exc.reason}")
        except URLError as exc:
            print(f"feishu webhook url error: msg={exc.reason}")
        except TimeoutError:
            print("feishu webhook timeout")

    def should_suppress_feishu(self, suppress_key):
        if not self.suppress_feishu_in_same_period or suppress_key is None:
            return False
        if suppress_key in self.sent_feishu_period_keys:
            return True
        self.sent_feishu_period_keys.add(suppress_key)
        return False

    def get_feishu_suppress_key(self, code, action_type):
        now = datetime.now()
        return code, action_type, now.year, now.month, now.day, now.hour, now.minute // 15

    def period_name(self, period):
        period_names = {
            KLType.K_15M: "15分钟",
            KLType.K_120M: "2小时",
            KLType.K_240M: "4小时",
            KLType.K_WEEK: "周线",
            KLType.K_MON: "月线",
            KLType.K_QUARTER: "季线",
        }
        return period_names.get(period, str(period))
