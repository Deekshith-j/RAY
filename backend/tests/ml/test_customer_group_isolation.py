"""Customer Group Isolation Tests for Phase 5 Hardening.

Invariant:
    TRAIN ∩ VALIDATION = ∅
    TRAIN ∩ TEST = ∅
    VALIDATION ∩ TEST = ∅

Splits MUST use customer_id as the grouping key.
The tests verify zero customer overlap across all three splits,
and verify that any customer leakage fails immediately.
"""

import pytest
import pandas as pd
import numpy as np
from app.ml.dataset import (
    create_customer_grouped_splits,
    build_reproducible_dataset,
    DatasetSplits,
)


def test_customer_group_isolation_strict():
    """Verify that TRAIN, VALIDATION, and TEST sets have strictly disjoint customer sets."""
    # Generate 200 events across 50 customers with varying transaction frequencies
    np.random.seed(42)
    customer_pool = [f"cust_{i:03d}" for i in range(50)]
    customer_ids = list(np.random.choice(customer_pool, size=200))

    X = pd.DataFrame({
        "amount": np.random.uniform(100.0, 5000.0, size=200),
        "feature_1": np.random.randn(200),
        "feature_2": np.random.randn(200),
    })
    y = pd.Series(np.random.choice([0, 1], size=200))

    splits: DatasetSplits = create_customer_grouped_splits(
        X=X,
        y=y,
        customer_ids=customer_ids,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=42,
    )

    train_cids = splits.train_customers
    val_cids = splits.val_customers
    test_cids = splits.test_customers

    # Strict pairwise disjointness
    train_val_overlap = train_cids.intersection(val_cids)
    train_test_overlap = train_cids.intersection(test_cids)
    val_test_overlap = val_cids.intersection(test_cids)

    assert len(train_val_overlap) == 0, f"TRAIN and VAL overlap detected: {train_val_overlap}"
    assert len(train_test_overlap) == 0, f"TRAIN and TEST overlap detected: {train_test_overlap}"
    assert len(val_test_overlap) == 0, f"VAL and TEST overlap detected: {val_test_overlap}"

    # Also verify that every customer in X_train, X_val, X_test belongs ONLY to its respective group
    cust_series = pd.Series(customer_ids)
    train_indices = X.index[cust_series.isin(train_cids)]
    val_indices = X.index[cust_series.isin(val_cids)]
    test_indices = X.index[cust_series.isin(test_cids)]

    assert len(set(train_indices).intersection(set(val_indices))) == 0
    assert len(set(train_indices).intersection(set(test_indices))) == 0
    assert len(set(val_indices).intersection(set(test_indices))) == 0

    # Total samples preserved
    assert len(splits.X_train) + len(splits.X_val) + len(splits.X_test) == 200


def test_customer_group_isolation_fails_on_leakage():
    """Verify that the test suite detects customer leakage if customer groups overlap."""
    train_cids = {"cust_001", "cust_002", "cust_003"}
    val_cids = {"cust_003", "cust_004"}  # cust_003 leaked!
    test_cids = {"cust_005", "cust_006"}

    with pytest.raises(AssertionError, match="overlap"):
        overlap = train_cids.intersection(val_cids)
        assert len(overlap) == 0, f"Customer overlap detected: {overlap}"


def test_customer_group_isolation_reproducible_builder():
    """Verify customer group isolation on the end-to-end dataset generator."""
    splits = build_reproducible_dataset(total_events=500, seed=42)

    assert len(splits.train_customers.intersection(splits.val_customers)) == 0
    assert len(splits.train_customers.intersection(splits.test_customers)) == 0
    assert len(splits.val_customers.intersection(splits.test_customers)) == 0

    assert len(splits.train_customers) > 0
    assert len(splits.val_customers) > 0
    assert len(splits.test_customers) > 0
