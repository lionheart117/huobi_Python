import datetime
from huobi.client.generic import GenericClient
from huobi.utils import *

def print_exchange_time():
    generic_client = GenericClient()
    ts = generic_client.get_exchange_timestamp()
    return datetime.datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S.%f')

if __name__ == '__main__':
    print(print_exchange_time())

