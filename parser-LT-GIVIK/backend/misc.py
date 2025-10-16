from typing import List

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


def create_linear_approximation(xs, ys):
    model = LinearRegression()
    X = np.array(xs).reshape(-1, 1)
    model.fit(X=X, y=ys)
    y_pred = model.predict(X=X)
    r2 = r2_score(ys, y_pred)
    slope = model.coef_[0]
    intercept = model.intercept_
    return r2, slope, intercept


def find_best_linear_subset(
    xs: List[float], ys: List[float], min_window_size: int = 10, step_size: int = 1
):
    """
    Find the best linear subset using a sliding window approach

    Parameters:
    - x: independent variable (1D array)
    - y: dependent variable (1D array)
    - min_window_size: minimum size of the linear segment to consider
    - step_size: step size for sliding the window

    Returns:
    - best_start, best_end: indices of the best linear segment
    - best_r2: R² score of the best segment
    """

    n = len(xs)
    best_r2 = -np.inf
    best_start = 0
    best_end = min_window_size

    slope, intercept = 0.0, 0.0
    for start in range(0, n - min_window_size, step_size):
        for end in range(start + min_window_size, n + 1, step_size):
            # Extract window
            x_window = xs[start:end].reshape(-1, 1)
            y_window = ys[start:end]

            # Fit linear regression
            r2, slope, intercept = create_linear_approximation(x_window, y_window)

            # Update best segment if better R² found
            if r2 > best_r2:
                best_r2 = r2
                best_start = start
                best_end = end

    return best_start, best_end, best_r2, slope, intercept
