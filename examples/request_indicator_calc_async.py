from futu import *
import time

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

class IndicatorCalcHandler(IndicatorCalcHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, content = super(IndicatorCalcHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print('error:', content)
            return ret_code, content
        print('calc result:', content)
        return RET_OK, content

quote_ctx.set_handler(IndicatorCalcHandler())

ret, kl_data, _ = quote_ctx.request_history_kline ('SH.688981', start='2026-06-01', end='2026-07-10',  ktype=KLType.K_120M)
#ret, kl_data, _ = quote_ctx.get_cur_kline('SH.688981', 50, KLType.K_120M, AuType.QFQ)
#ret, kl_data = quote_ctx.get_cur_kline('SH.688981', 25, KLType.K_DAY, AuType.QFQ)
if ret == RET_OK:
    ret, calc_id = quote_ctx.request_indicator_calc_async(
        'BOLL', IndicatorLangType.MYLANG, 'SH.688981', KLType.K_DAY, kl_data)
    if ret == RET_OK:
        print('calc_id:', calc_id)
    else:
        print('error:', calc_id)

time.sleep(5)
quote_ctx.close()
