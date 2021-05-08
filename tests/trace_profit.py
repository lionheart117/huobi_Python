from huobi.client.generic import GenericClient
from huobi.client.account import AccountClient
from huobi.client.trade import TradeClient
from huobi.constant import *
from keys import *
from huobi.client.market import MarketClient
from huobi.utils import *
import requests
import datetime
import time

def trace_profit(base_symbol, quote_symbol, amount, monitor_sleep_time, interval_upper_boundary_list, interval_rate_list, interval_delta_list,stop_loss_rate = 0.05, stop_profit_rate = float("inf"), buy_sleep_time = 5, sell_sleep_time = 5,buy_max_times = 1, sell_max_times = 20, test_mode = 0, test_price_vector = []):
    symbol = base_symbol + quote_symbol
    #illegal parameter
    if not (len(interval_upper_boundary_list) == len(interval_rate_list) == len(interval_delta_list)):
        return -1

    print("----------------------------------------------")
    print("Parameters:")
    print("1. base_symbol=%s, quote_symbol=%s, symbol=%s, amount=%f" % (base_symbol, quote_symbol, symbol, amount))
    print("2. stop_loss_rate=%f, stop_profit_rate=%f" % (stop_loss_rate, stop_profit_rate))
    print("3. monitor_sleep_time=%f" % monitor_sleep_time)
    print("4. interval_upper_boundary_list=%s" % interval_upper_boundary_list)
    print("5. interval_rate_list=%s" % interval_rate_list)
    print("6. interval_delta_list=%s" % interval_delta_list)
    print("7. buy_sleep_time=%d, sell_sleep_time=%d" % (buy_sleep_time, sell_sleep_time))
    print("8. buy_max_times=%d, sell_max_times=%d" % (buy_max_times, sell_max_times))
    print("9. test_mode=%d" % test_mode)
    print("----------------------------------------------\n")

    #Initial
    sell_dif_rate = -1
    hysteresis_cnt = 0
    check_times = 1
    market_client = MarketClient()
    trade_client = TradeClient(api_key=g_api_key, secret_key=g_secret_key)
    interval_flag_list = [0 for x in range(0,len(interval_upper_boundary_list))]   #generate interval flag list according to parameter

    #get buy order info from the buy order API
    if 1 == test_mode:
        symbol_start_price = test_price_vector[0]
        symbol_start_time  = 0
        #list_obj = market_client.get_market_trade(symbol)
        #symbol_start_price = list_obj[0].price
        #symbol_start_time  = list_obj[0].ts
    else:
        #create buy order
        [symbol_start_price, filled_amount, symbol_start_time] = must_buy_sell(OrderType.BUY_MARKET, base_symbol, quote_symbol, amount, 0, buy_max_times, buy_sleep_time)

    #SELL TEST:
    if test_mode == 2:
        print('TEST_MODE2: START SELL @time', datetime.datetime.fromtimestamp(symbol_start_time/1000).strftime('%Y-%m-%d %H:%M:%S.%f'),'\n')
        must_buy_sell(OrderType.SELL_MARKET, base_symbol, quote_symbol, filled_amount, 999999999, sell_max_times, sell_sleep_time)
        return 0

    print('START TRACING PROFIT from Price: %.8f @' % (symbol_start_price),datetime.datetime.fromtimestamp(symbol_start_time/1000).strftime('%Y-%m-%d %H:%M:%S.%f'),'\n')
    print('No.\tPRICE\t\tPRICE_DIF\tPRICE_DIF_RATE\tSELL_DIF_RATE\tFLAG_LIST\tCNT\tTIME\n')

    #monitor the latest price and price rate
    while(1):
        if test_mode:            
            symbol_current_price = test_price_vector[check_times]
            symbol_current_time  = 0
        else:
            try:
                list_obj = market_client.get_market_trade(symbol)
                symbol_current_price = list_obj[0].price
                symbol_current_time  = list_obj[0].ts
            except requests.exceptions.ProxyError as e:
                print(e)
                continue
            except requests.exceptions.ConnectionError as e:
                print(e)
                continue
            except requests.exceptions.ReadTimeout as e:
                print(e)
                continue            


        #get price dif and rate
        price_dif = symbol_current_price - symbol_start_price
        price_dif_rate = abs(price_dif / symbol_start_price)
        print("%d\t%0.8f\t%0.8f\t%0.8f%%\t%0.8f%%\t%s\t%d\t" % (check_times,symbol_current_price,price_dif,100*price_dif_rate,100*sell_dif_rate,interval_flag_list,hysteresis_cnt),datetime.datetime.fromtimestamp(symbol_current_time/1000).strftime('%Y-%m-%d %H:%M:%S.%f'))

        #stop loss
        if price_dif < 0 and price_dif_rate >= stop_loss_rate:
            print("------------Toggle stop loss------------\n")
            if not test_mode:
                must_buy_sell(OrderType.SELL_MARKET, base_symbol, quote_symbol, filled_amount, 999999999, sell_max_times, sell_sleep_time)
            return 0

        #stop profit
        if price_dif > 0 and price_dif_rate >= stop_profit_rate:
            print("------------Toggle stop profit------------\n")
            if not test_mode:
                must_buy_sell(OrderType.SELL_MARKET, base_symbol, quote_symbol, filled_amount, 999999999, sell_max_times, sell_sleep_time)
            return 0
        
        #update price rate and sell when get suitable profit
        if price_dif > 0 and price_dif_rate > sell_dif_rate:
            [sell_dif_rate, interval_flag_list, hysteresis_cnt] = sell_dif_rate_hysteresis(sell_dif_rate, interval_flag_list, hysteresis_cnt, price_dif, price_dif_rate, interval_upper_boundary_list, interval_rate_list, interval_delta_list)
        elif price_dif > 0 and price_dif_rate <= sell_dif_rate:
            print("------------Toggle get enough profit------------\n")
            if not test_mode:
                must_buy_sell(OrderType.SELL_MARKET, base_symbol, quote_symbol, filled_amount, 999999999, sell_max_times, sell_sleep_time)
            return 0

        #loop check times
        check_times += 1

        #loop sleep time
        time.sleep(monitor_sleep_time)


def sell_dif_rate_hysteresis(sell_dif_rate, interval_flag_list, hysteresis_cnt, price_dif, price_dif_rate, interval_upper_boundary_list, interval_rate_list, interval_delta_list):
    #illegal parameter
    if not (len(interval_upper_boundary_list) == len(interval_flag_list) == len(interval_rate_list) == len(interval_delta_list)):
        return -1
    
    for index_boundary, interval in enumerate(interval_upper_boundary_list):
        if price_dif > 0 and price_dif_rate < interval:
            break
    for index_flag, flag in enumerate(interval_flag_list):
        if flag == 0:
            break
    if index_boundary >= index_flag:
        index = index_boundary
    else:
        index = index_flag

    #print("index=%d\n" % index)

    if interval_flag_list[index] != 1:
        if index > 1:
            sell_dif_rate = interval_upper_boundary_list[index-2] + interval_rate_list[index-1] * hysteresis_cnt - (interval_rate_list[index-1] - interval_delta_list[index-1])
        elif index > 0:
            sell_dif_rate = interval_rate_list[index-1] * hysteresis_cnt - (interval_rate_list[index-1] - interval_delta_list[index-1])
        interval_flag_list[index] = 1
        hysteresis_cnt = 1

    if 0 == index and price_dif > 0 and price_dif_rate > (interval_rate_list[index] * hysteresis_cnt):
        sell_dif_rate = interval_rate_list[index] * hysteresis_cnt - (interval_rate_list[index] - interval_delta_list[index])
        hysteresis_cnt += 1
    elif index > 0 and price_dif > 0 and price_dif_rate > (interval_upper_boundary_list[index-1] + interval_rate_list[index] * hysteresis_cnt):
        sell_dif_rate = interval_upper_boundary_list[index-1] + interval_rate_list[index] * hysteresis_cnt - (interval_rate_list[index] - interval_delta_list[index])
        hysteresis_cnt += 1

    return [sell_dif_rate, interval_flag_list, hysteresis_cnt]

def must_buy_sell(order_type, base_symbol, quote_symbol, amount, price, max_times = 20, loop_sleep_time = 3):
#    account_client = AccountClient(api_key=g_api_key,
#                              secret_key=g_secret_key)
    trade_client = TradeClient(api_key=g_api_key, secret_key=g_secret_key)
    symbol = base_symbol + quote_symbol
    symbol_info = get_symbol_info(symbol)
    print("START TO %s @" % order_type, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
    while(max_times):
#        while(1):
#            try:
#                list_obj = account_client.get_balance(account_id=g_account_id)
#                break
#            except requests.exceptions.ProxyError as e:
#                print(e)
#                continue
#            except requests.exceptions.ConnectionError as e:
#                print(e)
#                continue
#            except requests.exceptions.ReadTimeout as e:
#                print(e)
#                continue            
#
#        for index in list_obj:
#            if index.currency == base_symbol and index.type == "trade":
#                account_amount = float(index.balance)

        while(1):
            try:
                order_id = trade_client.create_order(symbol, account_id=g_account_id, order_type=order_type, source=OrderSource.API, amount=precision_cali(amount, symbol_info.amount_precision), price=price)
                break
            except requests.exceptions.ProxyError as e:
                print(e)
                continue
            except requests.exceptions.ConnectionError as e:
                print(e)
                continue
            except requests.exceptions.ReadTimeout as e:
                print(e)
                continue            

        time.sleep(loop_sleep_time)

        while(1):
            try:
                orderObj = trade_client.get_order(order_id=order_id)
                break
            except requests.exceptions.ProxyError as e:
                print(e)
                continue
            except requests.exceptions.ConnectionError as e:
                print(e)
                continue
            except requests.exceptions.ReadTimeout as e:
                print(e)
                continue            
        
        if orderObj.state == "filled":
            print("No.%d Order state is %s" % (max_times, orderObj.state)) 
            print("No.%d Order filled amount is %s" % (max_times, orderObj.filled_amount))
            filled_price = precision_cali((float(orderObj.filled_cash_amount) / (float(orderObj.filled_amount) - float(orderObj.filled_fees))), symbol_info.price_precision)
            filled_amount = float(orderObj.filled_amount) - float(orderObj.filled_fees)
            return [filled_price, filled_amount, orderObj.finished_at]
        else:
            while(1):
                canceled_order_id = trade_client.cancel_order(symbol, order_id)
                if canceled_order_id == order_id:
                    LogInfo.output("Canceled order {id} done".format(id=canceled_order_id))
                    break
                else:
                    LogInfo.output("Canceled order {id} fail".format(id=canceled_order_id))
                    continue
            while(1):
                try:
                    canceled_orderObj = trade_client.get_order(order_id=canceled_order_id)
                    print("No.%d Canceled order filled amount is %s" % (max_times, canceled_orderObj.filled_amount))
                    break
                except requests.exceptions.ProxyError as e:
                    print(e)
                    continue
                except requests.exceptions.ConnectionError as e:
                    print(e)
                    continue
                except requests.exceptions.ReadTimeout as e:
                    print(e)
                    continue            
            

        max_times -= 1
        amount -= canceled_orderObj.filled_amount

def precision_cali(num,precision):
    num_str = format(num, '.20f')
    return float(num_str.split('.')[0] + '.' + num_str.split('.')[1][:precision])

def get_symbol_info(symbol):
    generic_client = GenericClient()
    while(1):
        try:
            list_obj = generic_client.get_exchange_symbols()
            break
        except requests.exceptions.ProxyError as e:
            print(e)
            continue
        except requests.exceptions.ConnectionError as e:
            print(e)
            continue
        except requests.exceptions.ReadTimeout as e:
            print(e)
            continue            

    if len(list_obj):
        for symbol_info_obj in list_obj:
            if symbol_info_obj.symbol == symbol:
                return symbol_info_obj


if __name__ == '__main__':
    import sys
    import numpy
    #print(sys.path)
    #print(g_account_id)
    #print(g_api_key)
    #print(g_secret_key)

    #testcase1
    #base_symbol = "btt"
    #quote_symbol = "usdt"
    #amount = 5
    #monitor_sleep_time = 0
    #interval_upper_boundary_list = [0.2, 0.5, 0.9]
    #interval_rate_list = [0.1, 0.15, 0.2]
    #interval_delta_list = [0.01, 0.01, 0.01]
    #stop_loss_rate = 0.05
    #stop_profit_rate = float("inf")
    ##stop_profit_rate = 0.2
    #buy_sleep_time = 5
    #sell_sleep_time = 5
    #buy_max_times = 1
    #sell_max_times = 20
    #test_mode = 1
    #test_price_vector = [1+numpy.sin(x) for x in numpy.arange(0.01,numpy.pi,0.01)]
    #trace_profit(base_symbol, quote_symbol, amount, monitor_sleep_time, interval_upper_boundary_list, interval_rate_list, interval_delta_list, stop_loss_rate, stop_profit_rate, buy_sleep_time, sell_sleep_time, buy_max_times, sell_max_times, test_mode, test_price_vector)

    #testcase2
    #base_symbol = "ekt"
    #quote_symbol = "usdt"
    #symbol = base_symbol + quote_symbol
    #amount = 6.000000
    #monitor_sleep_time = 1
    #interval_upper_boundary_list = [0.2, 0.5, 0.9]
    #interval_rate_list = [0.05, 0.1, 0.1]
    #interval_delta_list = [0.01, 0.01, 0.01]
    #stop_loss_rate = 0.05
    #stop_profit_rate = float("inf")
    ##stop_profit_rate = 0.2
    #buy_sleep_time = 5
    #sell_sleep_time = 5
    #buy_max_times = 1
    #sell_max_times = 20
    #test_mode = 0
    #test_price_vector = [1+numpy.sin(x) for x in numpy.arange(0.01,numpy.pi,0.01)]
    #trace_profit(base_symbol, quote_symbol, amount, monitor_sleep_time, interval_upper_boundary_list, interval_rate_list, interval_delta_list, stop_loss_rate, stop_profit_rate, buy_sleep_time, sell_sleep_time, buy_max_times, sell_max_times, test_mode, test_price_vector)
    ###must_sell(base_symbol, quote_symbol)
    ###print(precision_cali(float(3.1563126252505009988476953907816e-4), 6))
    ##get_symbol_info(symbol).print_object()

    #pratical function
    if "0" == sys.argv[1]:              #trace the most closely when less than 0.5
        interval_upper_boundary_list = [0.2, 0.5, 1.0]
        interval_rate_list = [0.05, 0.05, 0.1]
        stop_profit_rate = float("inf")
    elif "1" == sys.argv[1]:            #trace the most closely when less than 0.2
        interval_upper_boundary_list = [0.2, 0.5, 1.0]
        interval_rate_list = [0.05, 0.1, 0.1]
        stop_profit_rate = float("inf")
    elif "2" == sys.argv[1]:            #trace profit at 10% rate list
        interval_upper_boundary_list = [0.2, 0.5, 1.0]
        interval_rate_list = [0.1, 0.1, 0.1]
        stop_profit_rate = float("inf")
    elif "3" == sys.argv[1]:            #trace the most profit at risk
        interval_upper_boundary_list = [0.2, 0.5, 1.0]
        interval_rate_list = [0.05, 0.1, 0.2]
        stop_profit_rate = float("inf")
    elif "4" == sys.argv[1]:            #trace 20% profit
        interval_upper_boundary_list = [0.2, 0.5, 1.0]
        interval_rate_list = [0.05, 0.1, 0.2]
        stop_profit_rate = 0.2
    else:                               #trace the most closely when less than 0.5 
        interval_upper_boundary_list = [0.2, 0.5, 1.0]
        interval_rate_list = [0.05, 0.05, 0.1]
        stop_profit_rate = float("inf")

    base_symbol = sys.argv[2]
    quote_symbol = sys.argv[3]
    amount = float(sys.argv[4])
    sell_sleep_time = int(sys.argv[5])
    stop_loss_rate = float(sys.argv[6])
    symbol = base_symbol + quote_symbol
    monitor_sleep_time = 1
    interval_delta_list = [0.01, 0.01, 0.01]
    buy_sleep_time = 5
    buy_max_times = 1
    sell_max_times = 20
    test_mode = 0
    test_price_vector = []
    trace_profit(base_symbol, quote_symbol, amount, monitor_sleep_time, interval_upper_boundary_list, interval_rate_list, interval_delta_list, stop_loss_rate, stop_profit_rate, buy_sleep_time, sell_sleep_time, buy_max_times, sell_max_times, test_mode, test_price_vector)
