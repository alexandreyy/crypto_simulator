import argparse
from datetime import datetime
from multiprocessing import Process
import os
import time

from database.config import EXCHANGE_DATA
from database.data_record import DataRecord
from exchange.client import ExchangeClient
import numpy as np


def get_time():
    now = datetime.now()
    return int(now.strftime("%s"))


def retrieve_data(database_dir, exchange, coin, limit=5000):
    ERROR_INTERVAL = 5
    REQUEST_INTERVAL = 60

    time_now = get_time()
    database_dir = "%s/%s/%s/" % (database_dir, exchange, coin)
    if not os.path.exists(database_dir):
        os.makedirs(database_dir, exist_ok=True)

    client = ExchangeClient(exchange)
    day_index = int(time_now / 86400)
    data_record = DataRecord()
    data = dict()
    tfrecord_path = os.path.join(
        database_dir, "%d.tfrecords" % time_now)
    data_record.open(tfrecord_path)

    while True:
        try:
            r = client.get_orderbook(to_coin=coin, from_coin="USDT",
                                     limit=limit)
            time_now = get_time()

            current_day_index = int(time_now / 86400)
            if current_day_index > day_index:
                day_index = current_day_index
                data_record.close()
                tfrecord_path = os.path.join(
                    database_dir, "%d.tfrecords" % time_now)
                data_record.open(tfrecord_path)

            time_str = datetime.utcfromtimestamp(time_now).strftime(
                '%Y-%m-%d %H:%M:%S')
            r["asks"] = np.array(r["asks"])
            r["bids"] = np.array(r["bids"])

            if r is not None and "error" not in r:
                data['timestamp'] = time_now
                data['ask_price'] = r["asks"][:, 0]
                data['ask_qty'] = r["asks"][:, 1]
                data['bid_price'] = r["bids"][:, 0]
                data['bid_qty'] = r["bids"][:, 1]
                data_record.write(data)
                print("[%s][%s] %s - ask: %f | bid: %f" % (
                        time_str, exchange, coin,
                        r["asks"][0][0], r["bids"][0][0]))
                time.sleep(REQUEST_INTERVAL)
            else:
                if "error" in r:
                    raise Exception(r["error"])
                else:
                    raise Exception('Service error.')
        except Exception as e:
            print("[%s][%s] %s - Error in getting orderbook." % (
                time_str, exchange, coin))
            print(e)
            time.sleep(ERROR_INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Retrieve data from exchanges')
    parser.add_argument('database_dir', type=str,
                        help='directory where data will be saved')
    parser.add_argument('exchange', type=str, nargs='?',
                        default="", help='exchange used to retrieve data')
    parser.add_argument('coin', type=str, nargs='?',
                        default="", help='coin used to retrieve data')
    args = parser.parse_args()
    database_dir = str(args.database_dir)
    exchange = args.exchange
    coin = args.coin

    if exchange == "" or coin == "":
        processes = []
        for exchange in EXCHANGE_DATA:
            for coin in EXCHANGE_DATA[exchange]["coins"]:
                p = Process(
                    target=retrieve_data,
                    args=[database_dir, exchange, coin,
                          EXCHANGE_DATA[exchange]["limit"]])
                p.start()
                processes.append(p)

        for p in processes:
            p.join()
    else:
        retrieve_data(database_dir, exchange, coin)
