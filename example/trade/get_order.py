from huobi.client.trade import TradeClient
from huobi.constant import *
from huobi.utils import *

order_id = 273130955192309
trade_client = TradeClient(api_key=g_api_key, secret_key=g_secret_key)
orderObj = trade_client.get_order(order_id=order_id)
LogInfo.output("======= get order by order id : {order_id} =======".format(order_id=order_id))
orderObj.print_object()

