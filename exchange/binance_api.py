from binance.client import Client
from enum import Enum
import re
import time

import numpy as np


class BinanceOperation(Enum):
    GET_ORDERBOOK = 1
    GET_ORDERBOOK_TICKER = 2
    GET_ORDERBOOK_TICKERS = 3
    GET_RECENT_TRADES = 4


class BinanceClientWrapper:
    MAX_TRIES = 3
    SLEEP_TRIES = 1
    API_KEY = ""
    API_SECRET = ""

    def __init__(self):
        self._client = Client(self.API_KEY, self.API_SECRET)
        self._cache = dict()

    def get_orderbook(self, symbol="BTC_USDT", limit=1000):
        operation = BinanceOperation.GET_ORDERBOOK
        params = {
            "symbol": symbol.replace("_", ""),
            "limit": limit
        }
        return self._request(operation, params)

    def get_orderbook_ticker(self, symbol="BTC_USDT"):
        operation = BinanceOperation.GET_ORDERBOOK_TICKER
        params = {"symbol": symbol.replace("_", "")}
        return self._request(operation, params)

    def get_orderbook_tickers(self):
        operation = BinanceOperation.GET_ORDERBOOK_TICKERS
        return self._request(operation)

    def get_recent_trades(self, symbol="BTC_USDT", limit=500):
        operation = BinanceOperation.GET_RECENT_TRADES
        params = {
            "symbol": symbol.replace("_", ""),
            "limit": limit
        }
        return self._request(operation, params)

    def _request(self, operation, params=dict()):
        current_time = time.time()

        # Create cache key.
        key = str(operation)
        for p in params:
            key += str(params[p])

        if key in self._cache and \
                abs(current_time - self._cache[key]["time"]) < 60:
            return self._cache[key]["database"]
        else:
            i = 0
            while i < self.MAX_TRIES:
                try:
                    if operation == BinanceOperation.GET_ORDERBOOK:
                        response = self._client.get_order_book(
                            symbol=params["symbol"], limit=params["limit"])
                    elif operation == BinanceOperation.GET_ORDERBOOK_TICKER:
                        response = self._client.get_orderbook_ticker(
                            symbol=params["symbol"])
                    elif operation == BinanceOperation.GET_ORDERBOOK_TICKERS:
                        response = self._client.get_orderbook_tickers()
                    elif operation == BinanceOperation.GET_RECENT_TRADES:
                        response = self._client.get_recent_trades(
                            symbol=params["symbol"],
                            limit=params["limit"])[::-1]
                    break
                except Exception as e:
                    print(e)
                    if i < self.MAX_TRIES:
                        time.sleep(self.SLEEP_TRIES)
                        self._client = Client(self.API_KEY, self.API_SECRET)
                        current_time = time.time()
                        i += 1
                    else:
                        return None

        if key not in self._cache:
            self._cache[key] = dict()

        # Update cache.
        self._cache[key]["time"] = current_time
        self._cache[key]["database"] = response

        return response


class BinanceClient:
    LEGAL_LIMIT = [5, 10, 20, 50, 100, 500, 1000]
    TRADE_COINS = ["BTC", "BNB", "USDT"]

    def __init__(self):
        self._client = BinanceClientWrapper()
        self._coins = None
        self._symbols = None
        self._symbol_pattern = None

    def get_orderbook(self, to_coin="BTC", from_coin="USDT", limit=1000):
        symbol = to_coin + "_" + from_coin
        symbols = self.get_symbols()

        if limit <= 0:
            limit = 1
            request_limit = 5
        else:
            request_limit = 1000

            for i in self.LEGAL_LIMIT:
                if limit <= i:
                    request_limit = i
                    break

        if symbol in symbols:
            response = self._client.get_orderbook(
                symbol=symbol, limit=request_limit)
            orders = dict()
            orders["asks"] = np.array([[float(i[0]), float(i[1])]
                                       for i in response["asks"][:limit]])
            orders["bids"] = np.array([[float(i[0]), float(i[1])]
                                       for i in response["bids"][:limit]])
        elif from_coin + "_" + to_coin in symbols:
            symbol = from_coin + "_" + to_coin
            response = self._client.get_orderbook(
                symbol=symbol, limit=request_limit)
            orders = dict()
            orders["asks"] = np.array([
                [self._invert_value(float(i[0])), float(i[0]) * float(i[1])]
                for i in response["bids"][:limit]])
            orders["bids"] = np.array([
                [self._invert_value(float(i[0])), float(i[0]) * float(i[1])]
                for i in response["asks"][:limit]])
        else:
            from_coin_btc = from_coin + "_BTC"
            btc_from_coin = "BTC_" + from_coin
            to_coin_btc = to_coin + "_BTC"
            btc_to_coin = "BTC_" + to_coin

            if (from_coin_btc in symbols or btc_from_coin in symbols) and \
                    (to_coin_btc in symbols or btc_to_coin in symbols):
                if btc_from_coin in symbols:
                    response_1 = self._client.get_orderbook_ticker(
                        symbol=btc_from_coin)
                    bid_price_1 = float(response_1["bidPrice"])
                    ask_price_1 = float(response_1["askPrice"])
                else:
                    response_1 = self._client.get_orderbook_ticker(
                        symbol=from_coin_btc)
                    bid_price_1 = self._invert_value(
                        float(response_1["bidPrice"]))
                    ask_price_1 = self._invert_value(
                        float(response_1["askPrice"]))

                orders = dict()
                if to_coin_btc in symbols:
                    response_2 = self._client.get_orderbook(
                        symbol=to_coin_btc, limit=request_limit)
                    orders["asks"] = np.array(
                        [[float(i[0]) * ask_price_1, float(i[1])]
                         for i in response_2["asks"][:limit]])
                    orders["bids"] = np.array(
                        [[float(i[0]) * bid_price_1, float(i[1])]
                         for i in response_2["bids"][:limit]])
                else:
                    response_2 = self._client.get_orderbook(
                        symbol=btc_to_coin, limit=request_limit)
                    orders["bids"] = np.array(
                        [[self._invert_value(float(i[0])) * ask_price_1,
                          float(i[0]) * float(i[1])]
                         for i in response_2["asks"][:limit]])
                    orders["asks"] = np.array(
                        [[self._invert_value(float(i[0])) * bid_price_1,
                          float(i[0]) * float(i[1])]
                         for i in response_2["bids"][:limit]])
            else:
                return None

        return orders

    def get_recent_trades(self, to_coin="BTC", from_coin="USDT", limit=500):
        symbol = to_coin + "_" + from_coin
        symbols = self.get_symbols()

        if symbol in symbols:
            response = self._client.get_recent_trades(
                symbol=symbol, limit=limit)
            orders = np.array([
                [float(i["price"]), float(i["qty"]),
                 self._convert_to_timestamp(i["time"])]
                for i in response])
        elif from_coin + "_" + to_coin in symbols:
            symbol = from_coin + "_" + to_coin
            response = self._client.get_recent_trades(
                symbol=symbol, limit=limit)

            orders = np.array([
                [self._invert_value(float(i["price"])),
                 float(i["qty"]) * float(i["price"]),
                 self._convert_to_timestamp(i["time"])]
                for i in response])
        else:
            from_coin_btc = from_coin + "_BTC"
            btc_from_coin = "BTC_" + from_coin
            to_coin_btc = to_coin + "_BTC"
            btc_to_coin = "BTC_" + to_coin

            if (from_coin_btc in symbols or btc_from_coin in symbols) and \
                    (to_coin_btc in symbols or btc_to_coin in symbols):
                if btc_from_coin in symbols:
                    response_1 = self._client.get_recent_trades(
                        symbol=btc_from_coin, limit=1)
                    price_1 = float(response_1[0]["price"])
                else:
                    response_1 = self._client.get_recent_trades(
                        symbol=from_coin_btc, limit=1)
                    price_1 = self._invert_value(
                        float(response_1[0]["price"]))

                if to_coin_btc in symbols:
                    response_2 = self._client.get_recent_trades(
                        symbol=to_coin_btc, limit=limit)

                    orders = np.array([
                        [float(i["price"]) * price_1, float(i["qty"]),
                         self._convert_to_timestamp(i["time"])]
                        for i in response_2])
                else:
                    response_2 = self._client.get_recent_trades(
                        symbol=btc_to_coin, limit=limit)

                    orders = np.array([
                        [self._invert_value(float(i["price"])) * price_1,
                         float(i["price"]) * float(i["qty"]),
                         self._convert_to_timestamp(i["time"])]
                        for i in response_2])
            else:
                return None

        return orders

    def get_ticker(self, to_coin=None, from_coin=None):
        if to_coin is not None and from_coin is not None:
            symbol = to_coin + "_" + from_coin
            symbols = self.get_symbols()
            if symbol in symbols:
                response = self._client.get_orderbook_ticker(symbol=symbol)

                ticker = {
                    "bid_price": float(response["bidPrice"]),
                    "bid_qty": float(response["bidQty"]),
                    "ask_price": float(response["askPrice"]),
                    "ask_qty": float(response["askQty"]),
                }
            elif from_coin + "_" + to_coin in symbols:
                symbol = from_coin + "_" + to_coin
                response = self._client.get_orderbook_ticker(symbol=symbol)

                ticker = {
                    "ask_price":
                        self._invert_value(float(response["bidPrice"])),
                    "ask_qty":
                        float(response["bidQty"]) *
                        float(response["bidPrice"]),
                    "bid_price":
                        self._invert_value(float(response["askPrice"])),
                    "bid_qty":
                        float(response["askQty"]) *
                        float(response["askPrice"]),
                }
            else:
                from_coin_btc = from_coin + "_BTC"
                btc_from_coin = "BTC_" + from_coin
                to_coin_btc = to_coin + "_BTC"
                btc_to_coin = "BTC_" + to_coin

                if (from_coin_btc in symbols or btc_from_coin in symbols) and \
                        (to_coin_btc in symbols or btc_to_coin in symbols):
                    if btc_from_coin in symbols:
                        response_1 = self._client.get_orderbook_ticker(
                            symbol=btc_from_coin)
                        bid_price_1 = float(response_1["bidPrice"])
                        ask_price_1 = float(response_1["askPrice"])
                    else:
                        response_1 = self._client.get_orderbook_ticker(
                            symbol=from_coin_btc)
                        bid_price_1 = self._invert_value(
                            float(response_1["askPrice"]))
                        ask_price_1 = self._invert_value(
                            float(response_1["bidPrice"]))

                    if to_coin_btc in symbols:
                        response_2 = self._client.get_orderbook_ticker(
                                symbol=to_coin_btc)
                        bid_price_2 = float(response_2["bidPrice"])
                        ask_price_2 = float(response_2["askPrice"])
                        bid_qty = float(response_2["bidQty"])
                        ask_qty = float(response_2["askQty"])
                    else:
                        response_2 = self._client.get_orderbook_ticker(
                                symbol=btc_to_coin)
                        ask_price_2 = self._invert_value(
                            float(response_2["bidPrice"]))
                        bid_price_2 = self._invert_value(
                            float(response_2["askPrice"]))
                        ask_qty = float(response_2["bidQty"]) * \
                            float(response_2["bidPrice"])
                        bid_qty = float(response_2["askQty"]) * \
                            float(response_2["askPrice"])

                    ticker = {
                        "bid_price": bid_price_1 * bid_price_2,
                        "bid_qty": bid_qty,
                        "ask_price": ask_price_1 * ask_price_2,
                        "ask_qty": ask_qty,
                    }
                else:
                    return None
            return ticker
        else:
            tickers = []
            symbols = []
            responses = self._client.get_orderbook_tickers()

            for response in responses:
                to_coin, from_coin = self._split_symbol(response["symbol"])
                if response["symbol"] not in symbols:
                    ticker = {
                        "from_coin": from_coin,
                        "to_coin": to_coin,
                        "bid_price": float(response["bidPrice"]),
                        "bid_qty": float(response["bidQty"]),
                        "ask_price": float(response["askPrice"]),
                        "ask_qty": float(response["askQty"]),
                    }
                    symbols.append(response["symbol"])
                    tickers.append(ticker)

                symbol = from_coin + "_" + to_coin
                if symbol not in symbols:
                    ticker = {
                        "from_coin": to_coin,
                        "to_coin": from_coin,
                        "ask_price":
                            self._invert_value(float(response["bidPrice"])),
                        "ask_qty":
                            float(response["bidQty"]) *
                            float(response["bidPrice"]),
                        "bid_price":
                            self._invert_value(float(response["askPrice"])),
                        "bid_qty":
                            float(response["askQty"]) *
                            float(response["askPrice"]),
                    }

                    symbols.append(symbol)
                    tickers.append(ticker)

            return tickers

    def get_symbols(self):
        if self._symbols is None or self._coins is None:
            # Get symbols.
            self._symbols = []
            responses = self._client.get_orderbook_tickers()
            for response in responses:
                self._symbols.append(response["symbol"])
            self._symbols = sorted(self._symbols)

            # Get coins.
            self._coins = set()
            for symbol in self._symbols:
                for coin in self.TRADE_COINS:
                    if symbol.endswith(coin):
                        symbol = symbol[:-len(coin)]
                        self._coins.add(symbol)
                        break

            for coin in self.TRADE_COINS:
                self._coins.add(coin)

            self._coins = sorted(list(self._coins))

            # Update symbol list to use separator.
            for i in range(len(self._symbols)):
                to_coin, from_coin = self._split_symbol(self._symbols[i])
                self._symbols[i] = "%s_%s" % (to_coin, from_coin)
        return self._symbols

    def get_coins(self):
        if self._symbols is None or self._coins is None:
            self.get_symbols()
        return self._coins

    def _split_symbol(self, symbol):
        if "_" in symbol:
            coins = symbol.split("_")
            to_coin = coins[0]
            from_coin = coins[1]

            return to_coin, from_coin
        else:
            if self._symbol_pattern is None:
                coin_pattern = ""
                coins = self.get_coins()
                for coin in coins:
                    coin_pattern += coin + "|"
                coin_pattern = coin_pattern[:(len(coin_pattern) - 1)]
                self._symbol_pattern = '^(%s)(%s)$' % \
                    (coin_pattern, coin_pattern)
            try:
                result = re.search(self._symbol_pattern, symbol)
                to_coin = result.group(1)
                from_coin = result.group(2)

                return to_coin, from_coin
            except Exception as e:
                print("Error while parsing symbol to split coins.")
                print(e)
                return None

    def _invert_value(self, value):
        if value != 0:
            return 1.0 / value
        else:
            return 0.0

    def _convert_to_timestamp(self, value):
        value = int(int(value) / 1000)
        return value


if __name__ == "__main__":
    client = BinanceClient()
    r = client.get_ticker(to_coin="BTC", from_coin="USDT")
    r = client.get_ticker(to_coin="USDT", from_coin="BTC")
    r = client.get_ticker(to_coin="XEM", from_coin="USDT")
    r = client.get_ticker(to_coin="USDT", from_coin="XEM")
    re = client.get_ticker()
    r = [r for r in re if r["from_coin"] == "BTC" and r["to_coin"] == "XEM"]
    r = [r for r in re if r["from_coin"] == "XEM" and r["to_coin"] == "BTC"]
    r = client.get_orderbook(to_coin="BTC", from_coin="USDT", limit=2)
    r = client.get_orderbook(to_coin="USDT", from_coin="BTC", limit=2)
    r = client.get_orderbook(to_coin="XEM", from_coin="USDT", limit=2)
    r = client.get_orderbook(to_coin="USDT", from_coin="XEM", limit=2)
    r = client.get_recent_trades(to_coin="BTC", from_coin="USDT", limit=2)
    r = client.get_recent_trades(to_coin="USDT", from_coin="BTC", limit=2)
    r = client.get_recent_trades(to_coin="XEM", from_coin="USDT", limit=2)
    r = client.get_recent_trades(to_coin="USDT", from_coin="XEM", limit=2)
    print(r)
