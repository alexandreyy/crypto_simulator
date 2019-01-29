import numpy as np
from strategy.rsi import compute_rsi_series
from strategy.rsio import compute_k_d


def compute_srsi_series(data, period=None):
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

    srsi = (rsi - rsi_min) * 100.0 / rsi_range

    return srsi


class SRsiOscillatorStrategy:
    """ SRSIO strategy. """

    def __init__(self, periods=15, buy_rate=20, sell_rate=80,
                 k_oscillator_period=3, d_oscillator_period=3):
        self.periods = periods
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate
        self.k_oscillator_period = k_oscillator_period
        self.d_oscillator_period = d_oscillator_period

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result = compute_srsi_series(ticker_data[-self.periods:], self.periods)
        k, d = compute_k_d(result, self.k_oscillator_period,
                           self.d_oscillator_period)

        return result[0] <= self.buy_rate and k >= d

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result = compute_rsi_series(ticker_data[-self.periods:], self.periods)
        k, d = compute_k_d(result, self.k_oscillator_period,
                           self.d_oscillator_period)

        return result[0] >= self.sell_rate and k <= d
