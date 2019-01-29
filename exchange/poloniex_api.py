from datetime import datetime
from enum import Enum
from poloniex import Poloniex as Client
import time

import numpy as np


class PoloniexOperation(Enum):
    GET_ORDERBOOK = 1
    GET_ORDERBOOK_TICKER = 2
    GET_ORDERBOOK_TICKERS = 3
    GET_RECENT_TRADES = 4
    GET_COINS = 5


class PoloniexClientWrapper:
    MAX_TRIES = 3
    SLEEP_TRIES = 1
    API_KEY = ""
    API_SECRET = ""

    def __init__(self):
        self._client = Client(self.API_KEY, self.API_SECRET)
        self._cache = dict()

    def get_orderbook(self, symbol="BTC_USDT", limit=4612):
        operation = PoloniexOperation.GET_ORDERBOOK
        params = {
            "symbol": self._invert_symbol(symbol),
            "limit": limit
        }
        return self._request(operation, params)

    def get_orderbook_ticker(self, symbol="BTC_USDT"):
        operation = PoloniexOperation.GET_ORDERBOOK_TICKER
        params = {"symbol": self._invert_symbol(symbol)}
        return self._request(operation, params)

    def get_orderbook_tickers(self):
        operation = PoloniexOperation.GET_ORDERBOOK_TICKERS
        return self._request(operation)

    def get_recent_trades(self, symbol="BTC_USDT", limit=200):
        operation = PoloniexOperation.GET_RECENT_TRADES
        params = {
            "symbol": self._invert_symbol(symbol),
            "limit": limit
        }
        return self._request(operation, params)

    def get_coins(self):
        operation = PoloniexOperation.GET_COINS
        return self._request(operation)

    def _invert_symbol(self, symbol):
        coin_1, coin_2 = symbol.split("_")
        symbol = coin_2 + "_" + coin_1
        return symbol

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
                    if operation == PoloniexOperation.GET_ORDERBOOK:
                        response = self._client.returnOrderBook(
                            currencyPair=params["symbol"],
                            depth=params["limit"])
                    elif operation == PoloniexOperation.GET_ORDERBOOK_TICKER:
                        response = self._client.returnOrderBook(
                            currencyPair=params["symbol"], depth=1)
                    elif operation == PoloniexOperation.GET_ORDERBOOK_TICKERS:
                        response = self._client.returnOrderBook(
                            currencyPair="all", depth=1)
                    elif operation == PoloniexOperation.GET_RECENT_TRADES:
                        response = self._client.returnTradeHistoryPublic(
                            currencyPair=params["symbol"])[:params["limit"]]
                    elif operation == PoloniexOperation.GET_COINS:
                        response = self._client._private('returnBalances')
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


class PoloniexClient:
    def __init__(self):
        self._client = PoloniexClientWrapper()
        self._coins = None
        self._symbols = None

    def get_orderbook(self, to_coin="BTC", from_coin="USDT", limit=4612):
        symbol = to_coin + "_" + from_coin
        symbols = self.get_symbols()

        if symbol in symbols:
            response = self._client.get_orderbook(
                symbol=symbol, limit=limit)
            orders = dict()
            orders["asks"] = np.array([[float(i[0]), float(i[1])]
                                       for i in response["asks"]])
            orders["bids"] = np.array([[float(i[0]), float(i[1])]
                                       for i in response["bids"]])
        elif from_coin + "_" + to_coin in symbols:
            symbol = from_coin + "_" + to_coin
            response = self._client.get_orderbook(
                symbol=symbol, limit=limit)
            orders = dict()
            orders["asks"] = np.array([
                [self._invert_value(float(i[0])), float(i[0]) * float(i[1])]
                for i in response["bids"]])
            orders["bids"] = np.array([
                [self._invert_value(float(i[0])), float(i[0]) * float(i[1])]
                for i in response["asks"]])
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
                    bid_price_1 = float(response_1["bids"][0][0])
                    ask_price_1 = float(response_1["asks"][0][0])
                else:
                    response_1 = self._client.get_orderbook_ticker(
                        symbol=from_coin_btc)
                    bid_price_1 = self._invert_value(
                        float(response_1["bids"][0][0]))
                    ask_price_1 = self._invert_value(
                        float(response_1["asks"][0][0]))

                orders = dict()
                if to_coin_btc in symbols:
                    response_2 = self._client.get_orderbook(
                            symbol=to_coin_btc, limit=limit)
                    orders["asks"] = np.array(
                        [[float(i[0]) * ask_price_1, float(i[1])]
                         for i in response_2["asks"]])
                    orders["bids"] = np.array(
                        [[float(i[0]) * bid_price_1, float(i[1])]
                         for i in response_2["bids"]])
                else:
                    response_2 = self._client.get_orderbook(
                            symbol=btc_to_coin, limit=limit)
                    orders["bids"] = np.array(
                        [[self._invert_value(float(i[0])) * ask_price_1,
                          float(i[0]) * float(i[1])]
                         for i in response_2["asks"]])
                    orders["asks"] = np.array(
                        [[self._invert_value(float(i[0])) * bid_price_1,
                          float(i[0]) * float(i[1])]
                         for i in response_2["bids"]])
            else:
                return None

        return orders

    def get_recent_trades(self, to_coin="BTC", from_coin="USDT", limit=200):
        symbol = to_coin + "_" + from_coin
        symbols = self.get_symbols()

        if symbol in symbols:
            response = self._client.get_recent_trades(
                symbol=symbol, limit=limit)
            orders = np.array([
                [float(i["rate"]), float(i["amount"]),
                 self._convert_to_timestamp(i["date"])]
                for i in response])
        elif from_coin + "_" + to_coin in symbols:
            symbol = from_coin + "_" + to_coin
            response = self._client.get_recent_trades(
                symbol=symbol, limit=limit)

            orders = np.array([
                [self._invert_value(float(i["rate"])),
                 float(i["amount"]) * float(i["rate"]),
                 self._convert_to_timestamp(i["date"])]
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
                    price_1 = float(response_1[0]["rate"])
                else:
                    response_1 = self._client.get_recent_trades(
                        symbol=from_coin_btc, limit=1)
                    price_1 = self._invert_value(
                        float(response_1[0]["rate"]))

                if to_coin_btc in symbols:
                    response_2 = self._client.get_recent_trades(
                        symbol=to_coin_btc, limit=limit)

                    orders = np.array([
                        [float(i["rate"]) * price_1, float(i["amount"]),
                         self._convert_to_timestamp(i["date"])]
                        for i in response_2])
                else:
                    response_2 = self._client.get_recent_trades(
                        symbol=btc_to_coin, limit=limit)

                    orders = np.array([
                        [self._invert_value(float(i["rate"])) * price_1,
                         float(i["rate"]) * float(i["amount"]),
                         self._convert_to_timestamp(i["date"])]
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
                    "bid_price": float(response["bids"][0][0]),
                    "bid_qty": float(response["bids"][0][1]),
                    "ask_price": float(response["asks"][0][0]),
                    "ask_qty": float(response["asks"][0][1]),
                }
            elif from_coin + "_" + to_coin in symbols:
                symbol = from_coin + "_" + to_coin
                response = self._client.get_orderbook_ticker(symbol=symbol)

                ticker = {
                    "ask_price":
                        self._invert_value(float(response["bids"][0][0])),
                    "ask_qty":
                        float(response["bids"][0][1]) *
                        float(response["bids"][0][0]),
                    "bid_price":
                        self._invert_value(float(response["asks"][0][0])),
                    "bid_qty":
                        float(response["asks"][0][1]) *
                        float(response["asks"][0][0]),
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
                        bid_price_1 = float(response_1["bids"][0][0])
                        ask_price_1 = float(response_1["asks"][0][0])
                    else:
                        response_1 = self._client.get_orderbook_ticker(
                            symbol=from_coin_btc)
                        bid_price_1 = self._invert_value(
                            float(response_1["asks"][0][0]))
                        ask_price_1 = self._invert_value(
                            float(response_1["bids"][0][0]))

                    if to_coin_btc in symbols:
                        response_2 = self._client.get_orderbook_ticker(
                                symbol=to_coin_btc)
                        bid_price_2 = float(response_2["bids"][0][0])
                        ask_price_2 = float(response_2["asks"][0][0])
                        bid_qty = float(response_2["bids"][0][1])
                        ask_qty = float(response_2["asks"][0][1])
                    else:
                        response_2 = self._client.get_orderbook_ticker(
                                symbol=btc_to_coin)
                        ask_price_2 = self._invert_value(
                            float(response_2["bids"][0][0]))
                        bid_price_2 = self._invert_value(
                            float(response_2["asks"][0][0]))
                        ask_qty = float(response_2["bids"][0][1]) * \
                            float(response_2["bids"][0][0])
                        bid_qty = float(response_2["asks"][0][1]) * \
                            float(response_2["asks"][0][0])

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

            for symbol in responses:
                try:
                    response = responses[symbol]
                    symbol = self._client._invert_symbol(symbol)
                    to_coin, from_coin = self._split_symbol(symbol)
                    if symbol not in symbols:
                        ticker = {
                            "from_coin": from_coin,
                            "to_coin": to_coin,
                            "bid_price": float(response["bids"][0][0]),
                            "bid_qty": float(response["bids"][0][1]),
                            "ask_price": float(response["asks"][0][0]),
                            "ask_qty": float(response["asks"][0][1]),
                        }
                        symbols.append(symbol)
                        tickers.append(ticker)

                    symbol = from_coin + "_" + to_coin
                    if symbol not in symbols:
                        ticker = {
                            "from_coin": to_coin,
                            "to_coin": from_coin,
                            "ask_price":
                                self._invert_value(
                                    float(response["bids"][0][0])),
                            "ask_qty":
                                float(response["bids"][0][1]) *
                                float(response["bids"][0][0]),
                            "bid_price":
                                self._invert_value(
                                    float(response["asks"][0][0])),
                            "bid_qty":
                                float(response["asks"][0][1]) *
                                float(response["asks"][0][0]),
                        }

                        symbols.append(symbol)
                        tickers.append(ticker)
                except Exception:
                    continue

            return tickers

    def get_symbols(self):
        if self._symbols is None:
            self._symbols = []
            responses = self._client.get_orderbook_tickers()
            for response in responses:
                symbol = self._client._invert_symbol(response)
                self._symbols.append(symbol)
            self._symbols = sorted(self._symbols)

        return self._symbols

    def get_coins(self):
        if self._coins is None:
            responses = self._client.get_coins()
            self._coins = set()

            for response in responses:
                self._coins.add(response)

            self._coins = sorted(list(self._coins))

        return self._coins

    def _split_symbol(self, symbol):
        coins = symbol.split("_")
        to_coin = coins[0]
        from_coin = coins[1]

        return to_coin, from_coin

    def _invert_value(self, value):
        if value != 0:
            return 1.0 / value
        else:
            return 0.0

    def _convert_to_timestamp(self, value):
        value = int(time.mktime(datetime.strptime(
            value, "%Y-%m-%d %H:%M:%S").timetuple())) - 2 * 3600
        return value


if __name__ == "__main__":
    client = PoloniexClient()
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
