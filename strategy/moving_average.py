import numpy as np


class MovingAverageStrategy:
    """ Moving average strategy. """

    def __init__(self, periods=15, trade_fee=0):
        self.periods = periods
        self.trade_fee = trade_fee

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result = np.mean(ticker_data[-self.periods:])
        return (ticker_data[-1] * (1 + self.trade_fee) < result) and \
               (ticker_data[-1] > ticker_data[-2])

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result = np.mean(ticker_data[-self.periods:])
        return (ticker_data[-1] * (1 - self.trade_fee) > result) and \
               (ticker_data[-1] < ticker_data[-2])
