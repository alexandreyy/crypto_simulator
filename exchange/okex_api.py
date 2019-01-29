from okex.core import OKExAPI
from enum import Enum
import time

import numpy as np


class OkexOperation(Enum):
    GET_ORDERBOOK = 1
    GET_ORDERBOOK_TICKER = 2
    GET_ORDERBOOK_TICKERS = 3
    GET_RECENT_TRADES = 4
    GET_SYMBOLS = 5


class OkexClientWrapper:
    MAX_TRIES = 3
    SLEEP_TRIES = 1
    API_KEY = ""
    API_SECRET = ""

    def __init__(self):
        self._client = OKExAPI(self.API_KEY, self.API_SECRET)
        self._cache = dict()

    def get_orderbook(self, symbol="BTC_USDT", limit=200):
        operation = OkexOperation.GET_ORDERBOOK
        params = {
            "symbol": symbol.lower(),
            "limit": limit
        }
        return self._request(operation, params)

    def get_orderbook_ticker(self, symbol="BTC_USDT"):
        operation = OkexOperation.GET_ORDERBOOK_TICKER
        params = {"symbol": symbol.lower()}
        return self._request(operation, params)

    def get_orderbook_tickers(self):
        operation = OkexOperation.GET_ORDERBOOK_TICKERS
        return self._request(operation)

    def get_recent_trades(self, symbol="BTC_USDT", limit=60):
        operation = OkexOperation.GET_RECENT_TRADES
        params = {
            "symbol": symbol.lower(),
            "limit": limit
        }
        return self._request(operation, params)

    def get_symbols(self):
        operation = OkexOperation.GET_SYMBOLS
        return self._request(operation)

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
                    if operation == OkexOperation.GET_ORDERBOOK:
                        response = self._client.get(
                            endpoint="depth", symbol=params["symbol"])
                        response["asks"] = \
                            response["asks"][-(params["limit"]):][::-1]
                        response["bids"] = response["bids"][:params["limit"]]
                    elif operation == OkexOperation.GET_ORDERBOOK_TICKER:
                        response = self._client.get(
                            endpoint="depth", symbol=params["symbol"])
                        response["ask"] = response["asks"][::-1][0]
                        response["bid"] = response["bids"][0]
                    elif operation == OkexOperation.GET_ORDERBOOK_TICKERS:
                        response = \
                            self._client.get(endpoint="tickers")["tickers"]
                    elif operation == OkexOperation.GET_SYMBOLS:
                        response = \
                            self._client.get(endpoint="tickers")["tickers"]
                    elif operation == OkexOperation.GET_RECENT_TRADES:
                        response = self._client.get(
                                endpoint="trades", symbol=params["symbol"]
                            )[:params["limit"]][::-1]
                    break
                except Exception as e:
                    print(e)
                    if i < self.MAX_TRIES:
                        time.sleep(self.SLEEP_TRIES)
                        self._client = OKExAPI(self.API_KEY, self.API_SECRET)
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


class OkexClient:

    def __init__(self):
        self._client = OkexClientWrapper()
        self._coins = None
        self._symbols = None
        self._symbol_pattern = None

    def get_orderbook(self, to_coin="BTC", from_coin="USDT", limit=200):
        to_coin = self._translate_coin(to_coin)
        from_coin = self._translate_coin(from_coin)
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
                    bid_price_1 = float(response_1["bid"][0])
                    ask_price_1 = float(response_1["ask"][0])
                else:
                    response_1 = self._client.get_orderbook_ticker(
                        symbol=from_coin_btc)
                    bid_price_1 = self._invert_value(
                        float(response_1["bid"][0]))
                    ask_price_1 = self._invert_value(
                        float(response_1["ask"][0]))

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

    def get_recent_trades(self, to_coin="BTC", from_coin="USDT", limit=60):
        to_coin = self._translate_coin(to_coin)
        from_coin = self._translate_coin(from_coin)
        symbol = to_coin + "_" + from_coin
        symbols = self.get_symbols()

        if symbol in symbols:
            response = self._client.get_recent_trades(
                symbol=symbol, limit=limit)

            orders = np.array([
                [float(i["price"]), float(i["amount"]),
                 self._convert_to_timestamp(i["date_ms"])]
                for i in response])
        elif from_coin + "_" + to_coin in symbols:
            symbol = from_coin + "_" + to_coin
            response = self._client.get_recent_trades(
                symbol=symbol, limit=limit)

            orders = np.array([
                [self._invert_value(float(i["price"])),
                 float(i["amount"]) * float(i["price"]),
                 self._convert_to_timestamp(i["date_ms"])]
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
                        [float(i["price"]) * price_1, float(i["amount"]),
                         self._convert_to_timestamp(i["date_ms"])]
                        for i in response_2])
                else:
                    response_2 = self._client.get_recent_trades(
                        symbol=btc_to_coin, limit=limit)

                    orders = np.array([
                        [self._invert_value(float(i["price"])) * price_1,
                         float(i["price"]) * float(i["amount"]),
                         self._convert_to_timestamp(i["date_ms"])]
                        for i in response_2])
            else:
                return None

        return orders

    def get_ticker(self, to_coin=None, from_coin=None):
        to_coin = self._translate_coin(to_coin)
        from_coin = self._translate_coin(from_coin)

        if to_coin is not None and from_coin is not None:
            symbol = to_coin + "_" + from_coin
            symbols = self.get_symbols()
            if symbol in symbols:
                response = self._client.get_orderbook_ticker(symbol=symbol)

                ticker = {
                    "bid_price": float(response["bid"][0]),
                    "bid_qty": float(response["bid"][1]),
                    "ask_price": float(response["ask"][0]),
                    "ask_qty": float(response["ask"][1]),
                }
            elif from_coin + "_" + to_coin in symbols:
                symbol = from_coin + "_" + to_coin
                response = self._client.get_orderbook_ticker(symbol=symbol)

                ticker = {
                    "ask_price":
                        self._invert_value(float(response["bid"][0])),
                    "ask_qty":
                        float(response["bid"][1]) *
                        float(response["bid"][0]),
                    "bid_price":
                        self._invert_value(float(response["ask"][0])),
                    "bid_qty":
                        float(response["ask"][1]) *
                        float(response["ask"][0]),
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
                        bid_price_1 = float(response_1["bid"][0])
                        ask_price_1 = float(response_1["ask"][0])
                    else:
                        response_1 = self._client.get_orderbook_ticker(
                            symbol=from_coin_btc)
                        bid_price_1 = self._invert_value(
                            float(response_1["ask"][0]))
                        ask_price_1 = self._invert_value(
                            float(response_1["bid"][0]))

                    if to_coin_btc in symbols:
                        response_2 = self._client.get_orderbook_ticker(
                                symbol=to_coin_btc)
                        bid_price_2 = float(response_2["bid"][0])
                        ask_price_2 = float(response_2["ask"][0])
                        bid_qty = float(response_2["bid"][1])
                        ask_qty = float(response_2["ask"][1])
                    else:
                        response_2 = self._client.get_orderbook_ticker(
                                symbol=btc_to_coin)
                        ask_price_2 = self._invert_value(
                            float(response_2["bid"][0]))
                        bid_price_2 = self._invert_value(
                            float(response_2["ask"][0]))
                        ask_qty = float(response_2["bid"][1]) * \
                            float(response_2["bid"][0])
                        bid_qty = float(response_2["ask"][1]) * \
                            float(response_2["ask"][0])

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
                symbol = response["symbol"].upper()
                to_coin, from_coin = self._split_symbol(symbol)
                if symbol not in symbols:
                    ticker = {
                        "from_coin": from_coin,
                        "to_coin": to_coin,
                        "bid_price": float(response["buy"]),
                        "bid_qty": 0.0,
                        "ask_price": float(response["sell"]),
                        "ask_qty": 0.0,
                    }
                    symbols.append(symbol)
                    tickers.append(ticker)

                symbol = from_coin + "_" + to_coin
                if symbol not in symbols:
                    ticker = {
                        "from_coin": to_coin,
                        "to_coin": from_coin,
                        "ask_price":
                            self._invert_value(float(response["buy"])),
                        "ask_qty": 0.0,
                        "bid_price":
                            self._invert_value(float(response["sell"])),
                        "bid_qty": 0.0,
                    }

                    symbols.append(symbol)
                    tickers.append(ticker)

            return tickers

    def get_symbols(self):
        if self._symbols is None:
            self._symbols = []
            responses = self._client.get_symbols()
            for response in responses:
                self._symbols.append(response["symbol"].upper())
            self._symbols = sorted(self._symbols)

        return self._symbols

    def get_coins(self):
        if self._coins is None:
            self._symbols = self.get_symbols()
            self._coins = set()

            for symbol in self._symbols:
                to_coin, from_coin = self._split_symbol(symbol)
                self._coins.add(to_coin)
                self._coins.add(from_coin)

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
        value = int(int(value) / 1000)
        return value

    def _translate_coin(self, coin):
        if coin == "BCHABC":
            coin = "BCH"
        return coin


if __name__ == "__main__":
    client = OkexClient()
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
