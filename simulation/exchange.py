import random
import numpy as np

from database.config import EXCHANGE_DATA
from database.data_generator import sample_generator
# from simulation.logger import log


class SimulationExchange:
    orders = []
    delay_order = 0
    order_id = 0
    generators = dict()
    last_data = dict()
    timestamp = 0

    def __init__(self, balance, trade_fee=0.005, max_delay_order=10,
                 database_dir="resources", exchange="binance"):
        self.max_delay_order = max_delay_order
        self.balance = balance
        self.trade_fee = trade_fee
        self.database_dir = database_dir
        self.exchange = exchange

        coins = []
        for exchange in EXCHANGE_DATA:
            coins.extend(EXCHANGE_DATA[exchange]["coins"])
        self.coins = set(coins)

        for coin in self.coins:
            self.generators[coin] = sample_generator(database_dir, coin)

        for coin in EXCHANGE_DATA["binance"]["coins"]:
            self.last_data[coin] = [[]]
        self.increment_time()

    def get_orderbook(self, coin="BTC", delta_join=0.0005, size=30):
        limit_inferior = 0

        for exchange in EXCHANGE_DATA:
            if exchange != self.exchange:
                if coin in EXCHANGE_DATA[exchange]["coins"]:
                    limit_inferior += EXCHANGE_DATA[exchange]["limit"]
            else:
                break

        limit_superior = limit_inferior + EXCHANGE_DATA[self.exchange]["limit"]
        orderbook = self.last_data[coin][0]
        orderbook = orderbook[limit_inferior:limit_superior]
        orderbook_ask = orderbook[:, :2]
        orderbook_bid = orderbook[:, 2:]
        orderbook = np.zeros((size, 4))

        for data, p, q in zip([orderbook_ask, orderbook_bid], [0, 2], [1, 3]):
            i, j, k, price_qty, qty = (0, 0, 0, 0, 0.0000000001)

            while i < len(data) - 1 and k < size:
                if np.abs(data[i][0] - data[j][0]) / \
                        data[j][0] > delta_join:
                    orderbook[k, p] = price_qty / qty
                    orderbook[k, q] = qty
                    k += 1
                    j = i + 1
                    qty = 0.0000000001
                    price_qty = 0
                else:
                    price_qty += data[i][0] * data[i][1]
                    qty += data[i][1]

                i += 1

            i = k
            k = k - 1
            while i < size:
                orderbook[i, p] = orderbook[k, p]
                orderbook[i, q] = orderbook[k, q]
                i += 1

        return orderbook

    def get_orderbook_join(self, coin="BTC", delta_join=0.0005, size=30):
        orderbook = self.last_data[coin][0] + 0.0000000001
        orderbook_ask = np.sort(orderbook[:, :2], axis=0)
        orderbook_bid = np.sort(orderbook[:, 2:], axis=0)[::-1]
        orderbook = np.zeros((size, 4))

        for data, p, q in zip([orderbook_ask, orderbook_bid], [0, 2], [1, 3]):
            i, j, k, price_qty, qty = (0, 0, 0, 0, 0.0000000001)

            while i < len(data) - 1 and k < size:
                if np.abs(data[i][0] - data[j][0]) / \
                        data[j][0] > delta_join:
                    orderbook[k, p] = price_qty / qty
                    orderbook[k, q] = qty
                    k += 1
                    j = i + 1
                    qty = 0.0000000001
                    price_qty = 0
                else:
                    price_qty += data[i][0] * data[i][1]
                    qty += data[i][1]

                i += 1

            i = k
            k = k - 1
            while i < size:
                orderbook[i, p] = orderbook[k, p]
                orderbook[i, q] = orderbook[k, q]
                i += 1

        return orderbook

    def get_ticker(self, coin="BTC"):
        limit_inferior = 0

        for exchange in EXCHANGE_DATA:
            if exchange != self.exchange:
                if coin in EXCHANGE_DATA[exchange]["coins"]:
                    limit_inferior += EXCHANGE_DATA[exchange]["limit"]
            else:
                break

        orderbook = self.last_data[coin][0]
        ticker = orderbook[limit_inferior][2]

        return ticker

    def get_ticker_join(self, coin="BTC"):
        tickers = []
        limit_inferior = 0

        for exchange in EXCHANGE_DATA:
            if coin in EXCHANGE_DATA[exchange]["coins"]:
                orderbook = self.last_data[coin][0]
                ticker = orderbook[limit_inferior][2]
                limit_inferior += EXCHANGE_DATA[exchange]["limit"]
                tickers.append(ticker)

        # tickers = np.sort(tickers)[:4]
        ticker = np.mean(tickers)
        return ticker

    def get_coins(self):
        return EXCHANGE_DATA[self.exchange]["coins"]

    def get_balance(self, coin):
        """ Get balance. """

        return self.balance[coin]

    def increment_time(self):
        """ Increment simulation time. """

        max_timestamp = 0
        for coin in self.coins:
            # Data format: data type, interval.
            self.last_data[coin] = next(self.generators[coin])
            max_timestamp = max(self.last_data[coin][1], max_timestamp)

        sync = True
        while sync:
            sync = False

            for coin in self.coins:
                delta = max_timestamp - self.last_data[coin][1]

                while delta > 120:
                    self.last_data[coin] = next(self.generators[coin])
                    delta = max_timestamp - self.last_data[coin][1]

                if self.last_data[coin][1] > max_timestamp:
                    max_timestamp = self.last_data[coin][1]
                    sync = True

        self.timestamp = max_timestamp

    def get_timestamp(self):
        return self.timestamp

    def send_order(self, from_coin, to_coin, price, amount, order_type):
        """ Send order. """

        if self.balance[from_coin] > 0:
            if order_type == "buy":
                self.balance[from_coin] -= amount
#                 data_time = self.get_timestamp()
#                 log(data_time,
#                       "Send order to buy %f %s (%f %s) by $%d" %
#                       (amount / price, to_coin, amount, from_coin, price))
            else:
                self.balance[from_coin] -= amount
#                 data_time = self.get_timestamp()
#                 log(data_time, "Send order to sell %f %s (%f %s) by $%d" %
#                       (amount, from_coin, amount * price, to_coin, price))

            order = dict()
            order["id"] = self.order_id
            order["amount"] = amount
            order["price"] = price
            order["from_coin"] = from_coin
            order["to_coin"] = to_coin
            order["type"] = order_type
            self.order_id += 1
            self.orders.append(order)

    def has_order(self):
        """ Check if there is any order. """

        return len(self.orders) > 0

    def get_balance_total(self, coin="USDT"):
        """ Check if there is any order. """

        if coin == "USDT":
            amount = self.balance["USDT"]
            amount += self.balance["BTC"] * self.get_ticker()

            for order in self.orders:
                if order["from_coin"] == "USDT":
                    amount += order["amount"]
                else:
                    amount += order["amount"] * self.get_ticker()
        elif coin == "BTC":
            amount = self.balance["BTC"]
            amount += self.balance["USDT"] / self.get_ticker()

            for order in self.orders:
                if order["from_coin"] == "BTC":
                    amount += order["amount"]
                else:
                    amount += order["amount"] / self.get_ticker()
        else:
            amount = 0

        return amount

    def cancel_order(self, order_id):
        """ Cancel an order. """

        tmp_orders = []

        for order in self.orders:
            if order["id"] != order_id:
                tmp_orders.append(order)
            else:
                self.balance[order["from_coin"]] += order["amount"]
#                 data_time = self.get_timestamp()

#                 if order["type"] == "buy":
#                     log(data_time,
#                           "Cancelled order to buy %f %s (%f %s) by $%d." %
#                           (order["amount"] / order["price"], order["to_coin"]
#                            order["amount"], order["from_coin"],
#                            order["price"]))
#                 else:
#                     log(data_time,
#                           "Cancelled order to sell %f %s (%f %s) by $%d" %
#                           (order["amount"], order["from_coin"],
#                            order["amount"] * order["price"], order["to_coin"]
#                            order["price"]))

        self.orders = tmp_orders

    def cancel_orders(self, coin, order_type):
        """ Cancel orders. """

        orders = list(self.orders)

        for order in orders:
            if (order["type"] == order_type) and \
               ((order["to_coin"] == coin and order["type"] == "buy") or
                    (order["from_coin"] == coin and order["type"] == "sell")):
                self.cancel_order(order["id"])

    def execute_order(self):
        """ Simulate order execution. """

        if self.delay_order <= 0:
            order = self.orders.pop()

            if order["type"] == "buy":
                # data_time = self.get_timestamp()
                # log(data_time,
                #     "Order to buy %f %s (%f %s) by $%d executed." %
                #     (order["amount"] / order["price"], order["to_coin"],
                #      order["amount"], order["from_coin"], order["price"]))

                self.balance[order["to_coin"]] += \
                    order["amount"] / order["price"] * (1.0 - self.trade_fee)
            else:
                # data_time = self.get_timestamp()
                # log(data_time,
                #     "Order to sell %f %s (%f %s) by $%d executed." %
                #     (order["amount"], order["from_coin"],
                #      order["amount"] * order["price"], order["to_coin"],
                #      order["price"]))

                self.balance[order["to_coin"]] += \
                    order["amount"] * order["price"] * (1.0 - self.trade_fee)

            # Generate next delay.
            self.delay_order = random.randint(1, self.max_delay_order)
        else:
            self.delay_order -= 1
