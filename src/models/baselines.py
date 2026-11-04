"""
Baseline forecasting models for river water level prediction.
Provides Naive (Persistence), Moving Average, and Ridge Regression baselines.
"""

from typing import Optional
import numpy as np
from sklearn.linear_model import Ridge

from src.config import NUMERIC_FEATURES, TARGET_COL


class NaivePersistenceModel:
    """
    Persistence / Naive Forecast:
    Predicts that the future level at t+h equals the most recently observed level at t.
    """
    def __init__(self, target_idx: int = 0):
        self.target_idx = target_idx

    def fit(self, X: np.ndarray, y: np.ndarray):
        """No parameters to fit."""
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # X shape: (samples, sequence_length, features)
        # Most recent observation is at sequence_length - 1
        return X[:, -1, self.target_idx]


class MovingAverageModel:
    """
    Moving Average Forecast:
    Predicts the mean of the lookback window for the target feature.
    """
    def __init__(self, target_idx: int = 0, window: Optional[int] = None):
        self.target_idx = target_idx
        self.window = window

    def fit(self, X: np.ndarray, y: np.ndarray):
        """No parameters to fit."""
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # X shape: (samples, sequence_length, features)
        if self.window is not None and self.window < X.shape[1]:
            subset = X[:, -self.window :, self.target_idx]
        else:
            subset = X[:, :, self.target_idx]
        return np.mean(subset, axis=1)


class RidgeAutoregressiveModel:
    """
    Ridge Regression on flattened lookback features.
    Serves as a strong statistical machine-learning baseline.
    """
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.model = Ridge(alpha=alpha)

    def fit(self, X: np.ndarray, y: np.ndarray):
        # Flatten sequence: (samples, sequence_length * features)
        n_samples = X.shape[0]
        X_flat = X.reshape(n_samples, -1)
        self.model.fit(X_flat, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        n_samples = X.shape[0]
        X_flat = X.reshape(n_samples, -1)
        return self.model.predict(X_flat)
