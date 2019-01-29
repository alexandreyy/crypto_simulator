import numpy as np
from strategy.rsi import compute_rsi_series


def compute_srsi(data, period=None):
    """ Stochastic Relative Strength Index.

    SRSI = ((RSIt - RSI LOW) / (RSI HIGH - LOW RSI)) * 100
    """

    if period is None:
        period = len(data)

    rsi = compute_rsi_series(data, period)
    rsi_min = np.min(rsi)
    rsi_range = np.max(rsi) - rsi_min

    if rsi_range == 0:
        rsi_range = 1

    rsi = (rsi[-1] - rsi_min) * 100.0 / rsi_range

    return rsi


class SRsiStrategy:
    """ SRSI strategy. """

    def __init__(self, periods=15, buy_rate=20, sell_rate=80):
        self.periods = periods
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result = compute_srsi(ticker_data[-self.periods:], self.periods)
        return result <= self.buy_rate

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result = compute_srsi(ticker_data[-self.periods:], self.periods)
        return result >= self.sell_rate
