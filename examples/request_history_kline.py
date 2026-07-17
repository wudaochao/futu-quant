from futu import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data, page_req_key = quote_ctx.request_history_kline('SH.688981', start='2026-07-01', end='2026-07-11', ktype = KLType.K_120M, max_count=24, session=Session.ALL)  # 每页5个，请求第一页
if ret == RET_OK:
    print(data)
    print(data['code'][0])    # 取第一条的股票代码
    print(data['close'].values.tolist())   # 第一页收盘价转为 list
else:
    print('error:', data)
while page_req_key != None:  # 请求后面的所有结果
    print('*************************************')
    ret, data, page_req_key = quote_ctx.request_history_kline('SH.688981', start='2026-07-01', end='2026-07-11', ktype = KLType.K_120M, max_count=24, page_req_key=page_req_key, session=Session.ALL) # 请求翻页后的数据
    if ret == RET_OK:
        print(data)
    else:
        print('error:', data)
print('All pages are finished!')
quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽
