import pytest
import pandas as pd
from app.ml.dataset import create_customer_grouped_splits, build_reproducible_dataset


def test_customer_grouped_split_zero_leakage():
    # Construct synthetic customer IDs with multiple events per customer
    customer_ids = ["c1", "c1", "c2", "c2", "c3", "c4", "c5", "c6", "c7", "c8"]
    X = pd.DataFrame({
        "amount": [100.0] * 10,
        "feature_1": range(10),
    })
    y = pd.Series([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])

    splits = create_customer_grouped_splits(X, y, customer_ids, seed=42)

    # Verify zero customer intersection
    assert len(splits.train_customers.intersection(splits.val_customers)) == 0
    assert len(splits.train_customers.intersection(splits.test_customers)) == 0
    assert len(splits.val_customers.intersection(splits.test_customers)) == 0

    # Verify total samples match
    assert len(splits.X_train) + len(splits.X_val) + len(splits.X_test) == 10


def test_split_reproducibility():
    splits1 = build_reproducible_dataset(total_events=300, seed=42)
    splits2 = build_reproducible_dataset(total_events=300, seed=42)

    assert splits1.dataset_hash == splits2.dataset_hash
    assert len(splits1.X_train) == len(splits2.X_train)
    assert splits1.train_customers == splits2.train_customers
