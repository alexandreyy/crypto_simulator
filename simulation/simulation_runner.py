import argparse

from database.config import EXCHANGE_DATA
from simulation.exchange import SimulationExchange
from simulation.logger import log
from strategy.ichimoku import IchimokuStrategy
from strategy.linear_regression import LinearRegressionStrategy
from strategy.moving_average import MovingAverageStrategy
from strategy.moving_average_double import MovingAverageDoubleStrategy
from strategy.rsi import RsiStrategy
from strategy.rsio import RsiOscillatorStrategy
from strategy.srsi import SRsiStrategy
from strategy.srsio import SRsiOscillatorStrategy


class Strategy:
    def __init__(self, trade_fee=0):
        self.trade_fee = trade_fee
        self.strategy_rsi = RsiStrategy(15)
        self.strategy_rsio = RsiOscillatorStrategy(15)
        self.strategy_srsi = SRsiStrategy(15)
        self.strategy_srsi = SRsiOscillatorStrategy(15)
        self.strategy_ma = MovingAverageStrategy(15, trade_fee)
        self.strategy_mad = MovingAverageDoubleStrategy(
            period_1=9, period_2=21, trade_fee=trade_fee)
        self.strategy_lr = LinearRegressionStrategy(15, trade_fee)
        self.strategy_ich = IchimokuStrategy()

    def should_buy(self, ticker_data, orderbook_data):
        """ Check if we should buy. """

        return self.strategy_rsio.should_buy(ticker_data)

    def should_sell(self, ticker_data, orderbook_data):
        """ Check if we should sell. """

        return self.strategy_rsio.should_sell(ticker_data)


if __name__ == "__main__":
    """
    Run simulation.
    """

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

    # Simulation parameters.
    periods = 78  # in minutes.
    trade_fee = 0.001  # [0, 1]
    max_delay_order = 1  # in minutes.
    balance = dict()
    for coin in EXCHANGE_DATA["binance"]["coins"]:
        balance[coin] = 0
    base_coin = "USDT"
    balance[base_coin] = 100  # in dollars.
    coin = "BTC"
    init_trading_time = periods * 60 * 1  # in seconds.
#     log_balance_interval = 60 * 60 * 24  # in seconds.
    log_balance_interval = 60 * 60  # in seconds.

    # Initialize models.
    exchange = SimulationExchange(
        balance, trade_fee, max_delay_order, database_dir)
    last_time = init_time = exchange.get_timestamp()
    enable_trading = False
    trade_placed = False
    stop_loss_rate = 0.025  # [0, 1]
    wait_sell_time = 5  # in minutes.
    wait_sell_time_counter = wait_sell_time
    bought_price = 0
    strategy = Strategy(trade_fee)
    ticker_data = [0] * periods
    timestamp_data = [0] * periods
    timestamp_data[-1] = 999999
    period_sec = periods * 60
    period_sec_error = 300

    while True:
        # Get current data
        while True:
            exchange.increment_time()
            orderbook = exchange.get_orderbook()
            orderbook_data = exchange.get_orderbook_join()
            ticker_join = exchange.get_ticker_join()
            time_now = exchange.get_timestamp()
            ticker_data.pop(0)
            timestamp_data.pop(0)
            ticker_data.append(ticker_join)
            timestamp_data.append(time_now)

            if abs(exchange.get_timestamp() - timestamp_data[0]
                   - period_sec) < period_sec_error:
                break

        if enable_trading:
            # Check if we should buy or sell.
            wait_sell_time_counter += 1

            if strategy.should_buy(ticker_data, orderbook_data):
                from_coin = base_coin
                to_coin = coin
                exchange.cancel_orders(to_coin, "sell")

                if exchange.get_balance(from_coin) > 0:
                    # Send buy order.
                    exchange.send_order(from_coin, to_coin,
                                        orderbook[0][2],
                                        exchange.get_balance(from_coin),
                                        "buy")
                    bought_price = orderbook[0][2]
                    wait_sell_time_counter = 0
            else:
                stop_loss = orderbook[0][2] * (1 - trade_fee) <= \
                            bought_price * (1 + trade_fee - stop_loss_rate)

                if (strategy.should_sell(ticker_data, orderbook_data) and
                    wait_sell_time_counter >= wait_sell_time) or \
                   stop_loss:

                    from_coin = coin
                    to_coin = base_coin
                    exchange.cancel_orders(from_coin, "buy")

                    if exchange.get_balance(coin) > 0:
                        # Send sell order.
                        exchange.send_order(from_coin, to_coin,
                                            orderbook[0][2],
                                            exchange.get_balance(from_coin),
                                            "sell")

#             if strategy.should_buy(ticker_data, orderbook_data) or \
#                     strategy.should_sell(ticker_data, orderbook_data):
#                 log(exchange.get_timestamp(), "Balance %f %s." %
#                     (exchange.get_balance_total(base_coin), base_coin))
#                 time.sleep(1)

        # Simulate order execution.
        if exchange.has_order():
            exchange.execute_order()

        # Wait data initialization, before start trading.
        if not enable_trading and (exchange.get_timestamp() - init_time) >= \
                init_trading_time:

            # Enable trading.
            enable_trading = True
            log(exchange.get_timestamp(), "Start trading.")

        # Log balance in every interval set.
        if abs(exchange.get_timestamp() - last_time) > log_balance_interval:
            last_time = exchange.get_timestamp()
            log(exchange.get_timestamp(), "Balance %f %s." %
                (exchange.get_balance_total(base_coin), base_coin))
