import time
from futu import *

class RTDataTest(RTDataHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(RTDataTest, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("RTDataTest: error, msg: %s" % data)
            return RET_ERROR, data
        print("RTDataTest ", data) # RTDataTest 自己的处理逻辑
        print(data["close"][0])
        return RET_OK, data
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
handler = RTDataTest()
quote_ctx.set_handler(handler)  # 设置实时分时推送回调
ret, data = quote_ctx.subscribe(['SH.688981'], [SubType.RT_DATA], session=Session.ALL) # 订阅分时类型，OpenD 开始持续收到服务器的推送
if ret == RET_OK:
    print(data)
else:
    print('error:', data)
time.sleep(15)  # 设置脚本接收 OpenD 的推送持续时间为15秒
quote_ctx.close()   # 关闭当条连接，OpenD 会在1分钟后自动取消相应股票相应类型的订阅    
