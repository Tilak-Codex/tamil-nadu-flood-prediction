"""
Evaluation metrics for river water level forecasting.
Computes MAE, RMSE, R², and Nash-Sutcliffe Efficiency (NSE)
with guards for zero/low-variance target series.
"""

from typing import Dict, Optional
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_nse(y_true: np.ndarray, y_pred: np.ndarray, min_variance: float = 1e-4) -> Optional[float]:
    """
    Computes the Nash-Sutcliffe Efficiency (NSE):
        NSE = 1 - ( sum( (y_true - y_pred)^2 ) / sum( (y_true - mean(y_true))^2 ) )

    Range: (-inf, 1.0]. NSE = 1 is perfect prediction; NSE = 0 means model is only
    as good as the historical mean.
    
    IMPORTANT HYDROLOGICAL NOTE:
    If a river sensor flatlines (e.g. constant 160.22 m at Bhavani Bridge), the variance
    in the denominator sum((y_true - mean)^2) approaches 0. Any residual error then causes
    NSE to plunge to extreme negative values. This is an artifact of low-variance sensor
    readings, not necessarily catastrophic failure of the model.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    denom = np.sum((y_true - np.mean(y_true)) ** 2)
    if denom < min_variance:
        # Variance is virtually zero (flatlined sensor)
        return None

    numer = np.sum((y_true - y_pred) ** 2)
    return float(1.0 - (numer / denom))


def evaluate_forecasts(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, Optional[float]]:
    """Calculates MAE, RMSE, R2, and NSE for a set of forecasts."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if len(y_true) == 0:
        return {"mae": None, "rmse": None, "r2": None, "nse": None, "samples": 0}

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    # R2 requires at least 2 distinct values
    if np.var(y_true) > 1e-6:
        r2 = float(r2_score(y_true, y_pred))
    else:
        r2 = None

    nse = calculate_nse(y_true, y_pred)

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4) if r2 is not None else None,
        "nse": round(nse, 4) if nse is not None else None,
        "samples": len(y_true),
    }
