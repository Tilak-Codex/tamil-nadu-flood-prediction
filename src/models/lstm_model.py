"""
LSTM Model Architectures for River Water Level Forecasting.
Provides both the standalone Sequential architecture (from lstmmodel.py)
and the multi-station Functional architecture with station embeddings.
"""

import tensorflow as tf
from tensorflow.keras import Input, Model
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout,
    Embedding,
    Flatten,
    Concatenate,
)
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

from src.config import LEARNING_RATE


def build_sequential_lstm_model(
    sequence_length: int,
    num_features: int,
    learning_rate: float = LEARNING_RATE,
) -> Sequential:
    """
    Standard single-station Sequential LSTM architecture.
    Matches the user's initial design from lstmmodel.py.
    """
    model = Sequential([
        LSTM(units=64, return_sequences=True, input_shape=(sequence_length, num_features)),
        Dropout(0.2),
        LSTM(units=32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(8, activation="relu"),
        Dense(1, activation="linear"),
    ])

    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=[
            tf.keras.metrics.RootMeanSquaredError(name="rmse"),
            tf.keras.metrics.MeanAbsoluteError(name="mae"),
        ],
    )
    return model


def build_shared_lstm_model(
    sequence_length: int,
    num_numeric_features: int,
    num_stations: int,
    embedding_dim: int = 8,
    learning_rate: float = LEARNING_RATE,
) -> Model:
    """
    Multi-station Functional LSTM architecture:
    Preserves the LSTM(64) -> Dropout(0.2) -> LSTM(32) -> Dropout(0.2) stack,
    and merges it with a learned station entity embedding before the Dense head.
    This enables a single unified neural network to model spatial variations across
    all 35 Tamil Nadu monitoring stations.
    """
    # Branch 1: Hydrologic sequence input
    seq_input = Input(shape=(sequence_length, num_numeric_features), name="sequence_input")
    x = LSTM(units=64, return_sequences=True)(seq_input)
    x = Dropout(0.2)(x)
    x = LSTM(units=32, return_sequences=False)(x)
    x = Dropout(0.2)(x)

    # Branch 2: Station embedding input
    station_input = Input(shape=(1,), name="station_input")
    s = Embedding(
        input_dim=int(num_stations),
        output_dim=int(embedding_dim),
        name="station_embedding",
    )(station_input)
    s = Flatten()(s)

    # Merge branches
    merged = Concatenate()([x, s])

    # Dense head
    d = Dense(16, activation="relu")(merged)
    d = Dense(8, activation="relu")(d)
    output = Dense(1, activation="linear", name="water_level_forecast")(d)

    model = Model(inputs=[seq_input, station_input], outputs=output)

    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=[
            tf.keras.metrics.RootMeanSquaredError(name="rmse"),
            tf.keras.metrics.MeanAbsoluteError(name="mae"),
        ],
    )
    return model
