import argparse
from datetime import datetime
from glob import glob
import os

from database.config import EXCHANGE_DATA
from database.data_record import DataRecord
import numpy as np
import tensorflow as tf


def data_generator(database_dir, exchange, coin):
    database_dir = "%s/%s/%s/" % (database_dir, exchange, coin)
    tfrecord_paths = sorted(glob(os.path.join(database_dir, '*.tfrecords')))
    tfrecord_paths = tfrecord_paths[:(len(tfrecord_paths) - 1)]

    for tfrecord_path in tfrecord_paths:
        try:
            data_record = DataRecord(tfrecord_path)
            record_iterator = tf.python_io.tf_record_iterator(
                path=tfrecord_path)

            for string_record in record_iterator:
                data = data_record.decode(string_record)
                yield data
        except Exception:
            continue


def sample_generator(database_dir, coin, accept_interval=120):
    generators, exchange_data = (dict(), dict())

    for exchange in EXCHANGE_DATA:
        if coin in EXCHANGE_DATA[exchange]["coins"]:
            generators[exchange] = data_generator(database_dir, exchange, coin)

    last_data = False
    while not last_data:
        try:
            max_timestamp = 0
            for exchange in generators:
                exchange_data[exchange] = next(generators[exchange])
                max_timestamp = max(exchange_data[exchange]["timestamp"],
                                    max_timestamp)

            sync = True
            while sync:
                sync = False

                for exchange in generators:
                    delta = max_timestamp - \
                        exchange_data[exchange]["timestamp"]

                    while delta > accept_interval:
                        exchange_data[exchange] = next(generators[exchange])
                        delta = max_timestamp - \
                            exchange_data[exchange]["timestamp"]

                    if exchange_data[exchange]["timestamp"] > max_timestamp:
                        max_timestamp = exchange_data[exchange]["timestamp"]
                        sync = True

            x = []
            for exchange in generators:
                data = exchange_data[exchange]
                data_size = EXCHANGE_DATA[exchange]["limit"]

                for i in ["ask_price", "ask_qty", "bid_price", "bid_qty"]:
                    if len(data[i]) < data_size:
                        data[i] = np.hstack(
                            (data[i],
                             np.repeat(data[i][len(data[i]) - 1],
                                       data_size - len(data[i]))))
                x_exchange = np.vstack(
                    (data["ask_price"], data["ask_qty"],
                     data["bid_price"], data["bid_qty"])).transpose()
                x.append(x_exchange)

            yield np.vstack(x), max_timestamp
        except StopIteration:
            last_data = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Read data from exchange')
    parser.add_argument('database_dir', type=str,
                        help='directory where data will be read')
    parser.add_argument('coin', type=str, nargs='?',
                        default="BTC",
                        help='coin used to read data')
    args = parser.parse_args()
    database_dir = str(args.database_dir)
    coin = args.coin
    generator = sample_generator(database_dir, coin)

    last_data = False
    while not last_data:
        try:
            data, timestamp = next(generator)
            data = np.array(data)

            print("\nask_price:", data[0][0],
                  "\nask_qty:", data[0][1],
                  "\nbid_price:", data[0][2],
                  "\nbid_qty:", data[0][3],
                  "\ntimestamp: ", datetime.utcfromtimestamp(
                      timestamp).strftime('%Y-%m-%d %H:%M:%S'))
        except StopIteration:
            last_data = True
