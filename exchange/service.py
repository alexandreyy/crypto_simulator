from enum import IntEnum
from flask import Flask, request, jsonify
import time

from exchange.binance_api import BinanceClient
from exchange.bitfinex_api import BitfinexClient
from exchange.digifinex_api import DigifinexClient
from exchange.huobi_api import HuobiClient
from exchange.okex_api import OkexClient
from exchange.poloniex_api import PoloniexClient
from exchange.zb_api import ZbClient


class ExchangeId(IntEnum):
    BINANCE = 0
    BITFINEX = 1
    DIGIFINEX = 2
    HUOBI = 3
    OKEX = 4
    POLONIEX = 5
    ZB = 6

    def __str__(self):
        if self.value == self.BINANCE:
            return "binance"
        if self.value == self.BITFINEX:
            return "bitfinex"
        if self.value == self.DIGIFINEX:
            return "digifinex"
        if self.value == self.HUOBI:
            return "huobi"
        if self.value == self.OKEX:
            return "okex"
        if self.value == self.POLONIEX:
            return "poloniex"
        if self.value == self.ZB:
            return "zb"
        else:
            return ""


class RequestType(IntEnum):
    GET_ORDERBOOK = 1
    GET_ORDERBOOK_TICKER = 2
    GET_RECENT_TRADES = 3
    GET_COINS = 4
    GET_SYMBOLS = 5


MAX_TRIES = 3
SLEEP_TRIES = 5

# Create Flask application.
app = Flask(__name__)
clients = dict()

for exchange in ExchangeId:
    if exchange == ExchangeId.BINANCE:
        clients[exchange] = BinanceClient()
    elif exchange == ExchangeId.BITFINEX:
        clients[exchange] = BitfinexClient()
    elif exchange == ExchangeId.DIGIFINEX:
        clients[exchange] = DigifinexClient()
    elif exchange == ExchangeId.HUOBI:
        clients[exchange] = HuobiClient()
    elif exchange == ExchangeId.OKEX:
        clients[exchange] = OkexClient()
    elif exchange == ExchangeId.POLONIEX:
        clients[exchange] = PoloniexClient()
    elif exchange == ExchangeId.ZB:
        clients[exchange] = ZbClient()


@app.route('/get_coins', methods=['POST'])
def get_coins_handler():
    try:
        result = request_handler(RequestType.GET_COINS, request.get_json())
    except Exception as e:
        print(e)
        result = {"error": "Invalid json data."}
        result = jsonify(result)

    return result


@app.route('/get_symbols', methods=['POST'])
def get_symbols_handler():
    try:
        result = request_handler(RequestType.GET_SYMBOLS, request.get_json())
    except Exception as e:
        print(e)
        result = {"error": "Invalid json data."}
        result = jsonify(result)

    return result


@app.route('/get_ticker', methods=['POST'])
def get_ticker_handler():
    try:
        result = request_handler(RequestType.GET_ORDERBOOK_TICKER,
                                 request.get_json())
    except Exception as e:
        print(e)
        result = {"error": "Invalid json data."}
        result = jsonify(result)

    return result


@app.route('/get_orderbook', methods=['POST'])
def get_orderbook_handler():
    try:
        result = request_handler(RequestType.GET_ORDERBOOK,
                                 request.get_json())
    except Exception as e:
        print(e)
        result = {"error": "Invalid json data."}
        result = jsonify(result)

    return result


@app.route('/get_recent_trades', methods=['POST'])
def get_recent_trades_handler():
    try:
        result = request_handler(RequestType.GET_RECENT_TRADES,
                                 request.get_json())
    except Exception as e:
        print(e)
        result = {"error": "Invalid json data."}
        result = jsonify(result)

    return result


def get_exchange_id(exchange):
    for exchange_id in ExchangeId:
        if str(exchange_id) == exchange:
            return exchange_id

    return None


def request_handler(request_type, json_data):
    i = 0
    while i < MAX_TRIES:
        # Load data from json.
        try:
            exchange = get_exchange_id(json_data["exchange"])
            response = None

            if exchange is None:
                result = {"error": "Invalid exchange."}
            elif request_type == RequestType.GET_COINS:
                response = clients[exchange].get_coins()

                if response is None or len(response) < 0:
                    raise Exception('Error in getting coins.')
                else:
                    result = {"data": response}
            elif request_type == RequestType.GET_SYMBOLS:
                response = clients[exchange].get_symbols()

                if response is None or len(response) < 0:
                    raise Exception('Error in getting symbols.')
                else:
                    result = {"data": response}
            elif request_type == RequestType.GET_ORDERBOOK_TICKER:
                to_coin = json_data["to_coin"]
                from_coin = json_data["from_coin"]

                if to_coin == "" or from_coin == "":
                    to_coin = None
                    from_coin = None

                response = clients[exchange].get_ticker(
                    to_coin=to_coin, from_coin=from_coin)

                if response is None or len(response) < 0:
                    raise Exception('Error in getting ticker.')
                else:
                    result = {"data": response}
            elif request_type == RequestType.GET_ORDERBOOK:
                to_coin = json_data["to_coin"]
                from_coin = json_data["from_coin"]
                limit = int(json_data["limit"])

                if to_coin == "" or from_coin == "":
                    to_coin = None
                    from_coin = None

                response = clients[exchange].get_orderbook(
                    to_coin=to_coin, from_coin=from_coin, limit=limit)

                if response is None or "asks" not in response or \
                        "bids" not in response or len(response) < 0:
                    raise Exception('Error in getting orderbook.')
                else:
                    response["asks"] = response["asks"].tolist()
                    response["bids"] = response["bids"].tolist()
                    result = {"data": response}
            elif request_type == RequestType.GET_RECENT_TRADES:
                to_coin = json_data["to_coin"]
                from_coin = json_data["from_coin"]
                limit = int(json_data["limit"])

                if to_coin == "" or from_coin == "":
                    to_coin = None
                    from_coin = None

                response = clients[exchange].get_recent_trades(
                    to_coin=to_coin, from_coin=from_coin, limit=limit)

                if response is None or len(response) < 0:
                    raise Exception('Error in getting recent trades.')
                else:
                    result = {"data": response.tolist()}

            result = jsonify(result)
            break
        except Exception as e:
            error_message = "%s - data: %s " % (str(e), str(json_data))
            print(error_message)
            result = {"error": str(error_message)}
            result = jsonify(result)

            if i < MAX_TRIES:
                time.sleep(SLEEP_TRIES)
            i += 1

    return result


if __name__ == '__main__':
    # Run service on port 23450.
    app.run(host='0.0.0.0', port=23450)
