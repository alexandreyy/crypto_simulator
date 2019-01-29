import numpy as np


class MovingAverageDoubleStrategy:
    """ Double moving average strategy. """

    def __init__(self, period_1=9, period_2=21, trade_fee=0):
        if period_1 > period_2:
            self.period_max = period_1
            self.period_min = period_2
        else:
            self.period_max = period_2
            self.period_min = period_1

        self.trade_fee = trade_fee

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result_min = np.mean(ticker_data[-self.period_min:])
        result_max = np.mean(ticker_data[-self.period_max:])

        return (result_min * (1 + self.trade_fee) < result_max)

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result_min = np.mean(ticker_data[-self.period_min:])
        result_max = np.mean(ticker_data[-self.period_max:])

        return (result_min * (1 - self.trade_fee) > result_max)
