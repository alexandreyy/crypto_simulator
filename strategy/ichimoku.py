import numpy as np


def compute_ichimoku(data, tenkan=9, kijun=26, senkou=52,
                     senkou_lead=26, chikou=26):
    hi_tenkan = np.max(data[-tenkan:])
    lo_tenkan = np.min(data[-tenkan:])
    tenkan_sen = (hi_tenkan + lo_tenkan) / 2.0

    hi_kijun = np.max(data[-kijun:])
    lo_kijun = np.min(data[-kijun:])
    kijun_sen = (hi_kijun + lo_kijun) / 2.0

    lag_data = data[:(len(data) - senkou_lead)]
    hi_tenkan_lag = np.max(lag_data[-tenkan:])
    lo_tenkan_lag = np.min(lag_data[-tenkan:])
    tenkan_sen_lag = (hi_tenkan_lag + lo_tenkan_lag) / 2.0
    hi_kijun_lag = np.max(lag_data[-kijun:])
    lo_kijun_lag = np.min(lag_data[-kijun:])
    kijun_sen_lag = (hi_kijun_lag + lo_kijun_lag) / 2.0
    hi_senkou = np.max(lag_data[-senkou:])
    lo_senkou = np.min(lag_data[-senkou:])
    senkou_span_a = (tenkan_sen_lag + kijun_sen_lag) / 2.0
    senkou_span_b = (hi_senkou + lo_senkou) / 2.0

    chikou_span = data[-chikou]

    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span


class IchimokuStrategy:
    """ RSI strategy. """

    def __init__(self, tenkan=9, kijun=26, senkou=52, chikou=26):
        self.tenkan = tenkan
        self.kijun = kijun
        self.senkou = senkou
        self.chikou = chikou

    def should_buy(self, ticker_data):
        """ Check if we should buy. """
	"TODO: Implement me"
        return True

    def should_sell(self, ticker_data):
        """ Check if we should sell. """
	"TODO: Implement me"
        return True
