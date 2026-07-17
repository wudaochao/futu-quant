from futu import *
import time
class PriceReminderTest(PriceReminderHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, content = super(PriceReminderTest,self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("PriceReminderTest: error, msg: %s" % content)
            return RET_ERROR, content
        print("PriceReminderTest ", content) # PriceReminderTest 自己的处理逻辑
        return RET_OK, content
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
handler = PriceReminderTest()
quote_ctx.set_handler(handler)
ret, data = quote_ctx.get_market_snapshot(['HK.HSImain'])
if ret == RET_OK:
    bid_price = data['bid_price'][0]  # 获取实时买一价
    ask_price = data['ask_price'][0]  # 获取实时卖一价
    # 设置当卖一价低于（ask_price-1）时提醒
    ret_ask, ask_data = quote_ctx.set_price_reminder(code='HK.HSImain', op=SetPriceReminderOp.ADD, key=None, reminder_type=PriceReminderType.ASK_PRICE_DOWN, reminder_freq=PriceReminderFreq.ALWAYS, value=(ask_price-1), note='吴道超')
    if ret_ask == RET_OK:
        print('卖一价低于（ask_price-1）时提醒设置成功：', ask_data)
    else:
        print('error:', ask_data)
    # 设置当买一价高于（bid_price+1）时提醒
    ret_bid, bid_data = quote_ctx.set_price_reminder(code='HK.HSImain', op=SetPriceReminderOp.ADD, key=None, reminder_type=PriceReminderType.BID_PRICE_UP, reminder_freq=PriceReminderFreq.ALWAYS, value=(bid_price+1), note='吴道超')
    if ret_bid == RET_OK:
        print('买一价高于（bid_price+1）时提醒设置成功：', bid_data)
    else:
        print('error:', bid_data)
time.sleep(15)
quote_ctx.close()
