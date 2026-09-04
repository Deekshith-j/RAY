"""Preprocessing pipeline for RAY Recoverability ML.

CRITICAL INSTRUCTION:
Preprocessor must be fitted ONLY on training data. Never on validation or test sets.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from app.ml.config import ml_config


class RecoverabilityPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        numeric_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
    ):
        self.numeric_features = numeric_features or ml_config.NUMERIC_FEATURES
        self.categorical_features = categorical_features or ml_config.CATEGORICAL_FEATURES
        self.column_transformer: Optional[ColumnTransformer] = None
        self.is_fitted: bool = False
        self.feature_names_out_: List[str] = []

    def fit(self, X: pd.DataFrame, y=None):
        """Fit preprocessor EXCLUSIVELY on training data."""
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])

        self.column_transformer = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, self.numeric_features),
                ("cat", cat_pipeline, self.categorical_features),
            ],
            remainder="drop",
        )

        self.column_transformer.fit(X)
        self.is_fitted = True

        # Extract output feature names
        try:
            self.feature_names_out_ = list(self.column_transformer.get_feature_names_out())
        except Exception:
            self.feature_names_out_ = [f"feat_{i}" for i in range(self.column_transformer.transform(X[:2]).shape[1])]

        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using previously fitted transformers."""
        if not self.is_fitted or self.column_transformer is None:
            raise ValueError("RecoverabilityPreprocessor is not fitted yet!")
        return self.column_transformer.transform(X)

    def fit_transform(self, X: pd.DataFrame, y=None) -> np.ndarray:
        return self.fit(X, y).transform(X)
