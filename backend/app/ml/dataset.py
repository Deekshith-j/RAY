"""Dataset construction pipeline with Customer-Grouped splitting.

CRITICAL INSTRUCTION:
Customer-grouped split takes priority over ordinary stratification.
Ensures zero customer-level data leakage across Train, Validation, and Test sets.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Set, Tuple
import pandas as pd
import numpy as np

from app.ml.config import ml_config
from app.ml.features import extract_dataset_features
from app.simulator.generator import SyntheticDataGenerator


@dataclass
class DatasetSplits:
    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    train_customers: Set[str]
    val_customers: Set[str]
    test_customers: Set[str]
    dataset_hash: str
    total_samples: int


def compute_dataset_hash(X: pd.DataFrame, y: pd.Series) -> str:
    """Compute deterministic SHA-256 hash of dataset for provenance tracking."""
    data_summary = {
        "shape": list(X.shape),
        "target_sum": int(y.sum()),
        "columns": sorted(list(X.columns)),
        "first_amounts": [float(a) for a in X["amount"].head(10)],
    }
    return hashlib.sha256(json.dumps(data_summary, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def create_customer_grouped_splits(
    X: pd.DataFrame,
    y: pd.Series,
    customer_ids: List[str],
    train_ratio: float = ml_config.TRAIN_RATIO,
    val_ratio: float = ml_config.VAL_RATIO,
    test_ratio: float = ml_config.TEST_RATIO,
    seed: int = ml_config.SEED,
) -> DatasetSplits:
    """
    Split dataset into 70% Train, 15% Validation, and 15% Test
    strictly grouped by Customer ID.
    Zero customer overlap between splits.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Split ratios must sum to 1.0"
    assert len(X) == len(y) == len(customer_ids), "Mismatched lengths of X, y, and customer_ids"

    # Deterministic permutation of unique customers
    rng = np.random.RandomState(seed)
    unique_customers = np.array(sorted(list(set(customer_ids))))
    shuffled_customers = rng.permutation(unique_customers)

    n_customers = len(shuffled_customers)
    n_train = int(n_customers * train_ratio)
    n_val = int(n_customers * val_ratio)

    train_cids = set(shuffled_customers[:n_train])
    val_cids = set(shuffled_customers[n_train:n_train + n_val])
    test_cids = set(shuffled_customers[n_train + n_val:])

    # Strictly verify zero customer intersection
    assert len(train_cids.intersection(val_cids)) == 0, "Train-Val customer overlap!"
    assert len(train_cids.intersection(test_cids)) == 0, "Train-Test customer overlap!"
    assert len(val_cids.intersection(test_cids)) == 0, "Val-Test customer overlap!"

    # Create masks based on customer group
    cust_series = pd.Series(customer_ids, index=X.index)
    train_mask = cust_series.isin(train_cids)
    val_mask = cust_series.isin(val_cids)
    test_mask = cust_series.isin(test_cids)

    X_train = X[train_mask].reset_index(drop=True)
    y_train = y[train_mask].reset_index(drop=True)

    X_val = X[val_mask].reset_index(drop=True)
    y_val = y[val_mask].reset_index(drop=True)

    X_test = X[test_mask].reset_index(drop=True)
    y_test = y[test_mask].reset_index(drop=True)

    d_hash = compute_dataset_hash(X, y)

    return DatasetSplits(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        train_customers=train_cids,
        val_customers=val_cids,
        test_customers=test_cids,
        dataset_hash=d_hash,
        total_samples=len(X),
    )


def build_reproducible_dataset(
    total_events: int = 50000,
    seed: int = ml_config.SEED,
) -> DatasetSplits:
    """
    Generate synthetic dataset and produce deterministic customer-grouped splits.
    """
    generator = SyntheticDataGenerator(seed=seed)
    dataset = generator.generate_dataset(total_events=total_events)
    X, y, customer_ids = extract_dataset_features(dataset)
    return create_customer_grouped_splits(X, y, customer_ids, seed=seed)
