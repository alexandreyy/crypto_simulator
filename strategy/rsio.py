import numpy as np
from strategy.rsi import compute_rsi_series


def compute_k_series(data, filter_size=0, k_size=0):
    """ Compute K series. """

    data_size = len(data)

    if filter_size > data_size or filter_size == 0:
        filter_size = data_size

    if k_size > data_size or k_size == 0:
        k_size = filter_size

    k_list = []

    for i in range(k_size):
        try:
            min_data = np.min(data[i:(filter_size + i)])
            range_data = np.max(data[i:(filter_size + i)]) - min_data
            if range_data == 0:
                range_data = 1.0

            k = (data[i] - min_data) / range_data
            k_list.append(k)
        except Exception:
            break

    return k_list


def compute_k_d(data, k_size, d_size):
    """ Compute K and D. """

    data_size = len(data)
    if k_size > data_size:
        k_size = data_size

    if d_size > data_size:
        d_size = data_size

    k_series = compute_k_series(data, k_size)
    k = k_series[-1]
    d = np.mean(k_series[:d_size])

    return k, d


class RsiOscillatorStrategy:
    """ RSIO strategy. """

    def __init__(self, periods=15, buy_rate=20, sell_rate=80,
                 k_oscillator_period=3, d_oscillator_period=3):
        self.periods = periods
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate
        self.k_oscillator_period = k_oscillator_period
        self.d_oscillator_period = d_oscillator_period

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result = compute_rsi_series(ticker_data[-self.periods:], self.periods)
        k, d = compute_k_d(result, self.k_oscillator_period,
                           self.d_oscillator_period)

        return result[0] <= self.buy_rate and k >= d

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result = compute_rsi_series(ticker_data[-self.periods:], self.periods)
        k, d = compute_k_d(result, self.k_oscillator_period,
                           self.d_oscillator_period)

        return result[0] >= self.sell_rate and k <= d
