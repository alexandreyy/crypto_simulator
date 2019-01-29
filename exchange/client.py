import json
import requests


class ExchangeClient:

    def __init__(self, exchange="binance", api_url='http://localhost:23450'):
        self.api_url = api_url
        self.exchange = exchange

    def get_coins(self, exchange=None):
        url = self.api_url + '/get_coins'

        if exchange is None:
            exchange = self.exchange

        data = """
            {
                "exchange": "%s"
            } """ % exchange

        r = self._request(url, data)
        if "data" in r:
            return r["data"]
        else:
            print("Error: " + r["error"])
            return None

    def get_symbols(self, exchange=None):
        url = self.api_url + '/get_symbols'

        if exchange is None:
            exchange = self.exchange

        data = """
            {
                "exchange": "%s"
            } """ % exchange

        r = self._request(url, data)
        if "data" in r:
            return r["data"]
        else:
            print("Error: " + r["error"])
            return None

    def get_ticker(self, to_coin="", from_coin="", exchange=None):
        url = self.api_url + '/get_ticker'

        if exchange is None:
            exchange = self.exchange

        data = """
            {
                "exchange": "%s",
                "to_coin": "%s",
                "from_coin": "%s"
            } """ % (exchange, to_coin, from_coin)

        r = self._request(url, data)
        if "data" in r:
            return r["data"]
        else:
            print("Error: " + r["error"])
            return None

    def get_orderbook(self, to_coin="BTC", from_coin="USDT", limit=5000,
                      exchange=None):
        url = self.api_url + '/get_orderbook'

        if exchange is None:
            exchange = self.exchange

        data = """
            {
                "exchange": "%s",
                "to_coin": "%s",
                "from_coin": "%s",
                "limit": "%s"
            } """ % (exchange, to_coin, from_coin, str(limit))

        r = self._request(url, data)
        if "data" in r:
            return r["data"]
        else:
            print("Error: " + r["error"])
            return None

    def get_recent_trades(self, to_coin="BTC", from_coin="USDT", limit=5000,
                          exchange=None):
        url = self.api_url + '/get_recent_trades'

        if exchange is None:
            exchange = self.exchange

        data = """
            {
                "exchange": "%s",
                "to_coin": "%s",
                "from_coin": "%s",
                "limit": "%s"
            } """ % (exchange, to_coin, from_coin, str(limit))

        r = self._request(url, data)
        if "data" in r:
            return r["data"]
        else:
            print("Error: " + r["error"])
            return None

    def _request(self, url, data):
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        try:
            r = requests.post(url, data=data, headers=headers)
            r = json.loads(r.text)
        except Exception as e:
            print (e)
            print ("Connection with HTTP service failed.")

        return r


if __name__ == '__main__':
    client = ExchangeClient()
    r = client.get_coins()
    r = client.get_symbols()
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
