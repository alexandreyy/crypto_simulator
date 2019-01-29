import numpy as np


def compute_mse(current_price, gt_price, pred_price):
    alpha = 0.00001
    square_error = np.square(
        (gt_price - pred_price + alpha) / (current_price + alpha))
    mse = np.mean(square_error)
    return mse
