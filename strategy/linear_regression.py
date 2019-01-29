from sklearn import linear_model

import numpy as np


def compute_linear_regression(data, time_sequence=None):
    """ Compute linear regression. """

    if time_sequence is None:
        time_sequence = range(len(data))

    regr = linear_model.LinearRegression()
    data_X = np.array(time_sequence[:len(data)]).reshape(-1, 1)
    regr.fit(data_X, data)
    result = regr.predict(np.array([len(data) + 5]).reshape(-1, 1))[0]

    return result


class LinearRegressionStrategy:
    """ Linear regression strategy. """

    def __init__(self, periods=15, trade_fee=0):
        self.periods = periods
        self.trade_fee = trade_fee
        self.time_sequence = range(periods)

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result = compute_linear_regression(
            ticker_data[-self.periods:], self.time_sequence)

        return result * (1 + self.trade_fee) > ticker_data[-1]

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result = compute_linear_regression(
            ticker_data[-self.periods:], self.time_sequence)

        return result * (1 - self.trade_fee) < ticker_data[-1]
