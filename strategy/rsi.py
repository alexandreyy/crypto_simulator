import numpy as np
from six.moves import range
from six.moves import zip


def compute_rsi_series(data, period=None):
    """ Compute RSI series. """

    if period is None:
        period = len(data)

    period = int(period)
    changes = [data_tup[1] - data_tup[0]
               for data_tup in zip(data[::1], data[1::1])]

    filtered_gain = [val < 0 for val in changes]
    gains = [0 if filtered_gain[idx] else changes[idx]
             for idx in range(0, len(filtered_gain))]

    filtered_loss = [val > 0 for val in changes]
    losses = [0 if filtered_loss[idx] else abs(changes[idx])
              for idx in range(0, len(filtered_loss))]

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    rsi = []
    if avg_loss == 0:
        rsi_value = 100
    else:
        rs = avg_gain / avg_loss

        if 1 + rs == 0:
            if period > 1:
                avg_gain = np.mean(gains[:(period - 1)])
                avg_loss = np.mean(losses[:(period - 1)])
                rs = avg_gain / avg_loss

            if 1 + rs == 0:
                rsi_value = 100 - (100 / (1 + rs + 0.000001))
            else:
                rsi_value = 100 - (100 / (1 + rs))
        else:
            rsi_value = 100 - (100 / (1 + rs))

    rsi.append(rsi_value)

    for idx in range(1, len(data) - period):
        avg_gain = ((avg_gain * (period - 1) +
                    gains[idx + (period - 1)]) / period)
        avg_loss = ((avg_loss * (period - 1) +
                    losses[idx + (period - 1)]) / period)

        if avg_loss == 0:
            rsi_value = 100
        else:
            rs = avg_gain / avg_loss

            if 1 + rs == 0:
                if period > 1:
                    avg_gain = ((avg_gain * (period - 2) +
                                 gains[idx + (period - 2)]) / period)
                    avg_loss = ((avg_loss * (period - 2) +
                                 losses[idx + (period - 2)]) / period)
                    rs = avg_gain / avg_loss
                if 1 + rs == 0:
                    rsi_value = 100 - (100 / (1 + rs + 0.000001))
                else:
                    rsi_value = 100 - (100 / (1 + rs))
            else:
                rsi_value = 100 - (100 / (1 + rs))

        rsi.append(rsi_value)

    return rsi[::-1]


def compute_rsi(data, period=None):
    """ Relative Strength Index.

    RSI = 100 - (100 / 1 + (prevGain/prevLoss))
    """

    if period is None:
        period = len(data)

    rsi = compute_rsi_series(data, period)[-1]
    return rsi


class RsiStrategy:
    """ RSI strategy. """

    def __init__(self, periods=15, buy_rate=20, sell_rate=80):
        self.periods = periods
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate

    def should_buy(self, ticker_data):
        """ Check if we should buy. """

        result = compute_rsi(ticker_data[-self.periods:], self.periods)
        return result <= self.buy_rate

    def should_sell(self, ticker_data):
        """ Check if we should sell. """

        result = compute_rsi(ticker_data[-self.periods:], self.periods)
        return result >= self.sell_rate
