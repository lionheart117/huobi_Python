from huobi.client.generic import GenericClient
from huobi.utils import *

def get_usdt_symbols():
    usdt_symbols = []
    generic_client = GenericClient()
    list_obj = generic_client.get_exchange_symbols()
    if len(list_obj):
        for symb in list_obj:
            if symb.quote_currency == 'usdt':
                usdt_symbols.append(symb.symbol)
    return usdt_symbols

if __name__ == '__main__':
    usdt_symbols = get_usdt_symbols()
    print('symbol number are %d\n' % len(usdt_symbols))
    print(usdt_symbols)
