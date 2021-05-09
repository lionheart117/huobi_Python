from huobi.client.trade import TradeClient
from huobi.constant import *
from huobi.utils import *
from keys.py import *


symbol_test = "ftiusdt"


trade_client = TradeClient(g_api_key, g_secret_key)
order_id = trade_client.create_order(symbol=symbol_test, account_id=g_account_id, order_type=OrderType.SELL_LIMIT, source=OrderSource.API, amount=1.0, price=50000)
LogInfo.output("created order id : {id}".format(id=order_id))


orderObj = trade_client.get_order(order_id=order_id)
LogInfo.output("======= get order by order id : {order_id} =======".format(order_id=order_id))
orderObj.print_object()

#canceled_order_id = trade_client.cancel_order(symbol_test, order_id)
#if canceled_order_id == order_id:
#    LogInfo.output("cancel order {id} done".format(id=canceled_order_id))
#else:
#    LogInfo.output("cancel order {id} fail".format(id=canceled_order_id))
