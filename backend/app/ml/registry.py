"""Model registry for persisting and loading model artifacts and metadata."""

import json
from pathlib import Path
from typing import Tuple, Any, Optional
import joblib

from app.ml.config import ml_config
from app.ml.preprocessing import RecoverabilityPreprocessor
from app.ml.schemas import ModelMetadata


class ModelRegistry:
    def __init__(self, artifacts_dir: Optional[Path] = None):
        self.artifacts_dir = artifacts_dir or ml_config.ARTIFACTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.artifacts_dir / "best_model.joblib"
        self.preprocessor_path = self.artifacts_dir / "preprocessor.joblib"
        self.metadata_path = self.artifacts_dir / "metadata.json"

    def save_artifacts(
        self,
        model: Any,
        preprocessor: RecoverabilityPreprocessor,
        metadata: ModelMetadata,
    ) -> None:
        """Persist model, preprocessor, and metadata."""
        joblib.dump(model, self.model_path)
        joblib.dump(preprocessor, self.preprocessor_path)

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))

    def load_artifacts(self) -> Tuple[Any, RecoverabilityPreprocessor, ModelMetadata]:
        """Load active production model, preprocessor, and metadata."""
        if not self.model_path.exists() or not self.preprocessor_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Model artifacts not found in {self.artifacts_dir}. Please run 'python -m app.ml.train' first."
            )

        model = joblib.load(self.model_path)
        preprocessor = joblib.load(self.preprocessor_path)

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)
            metadata = ModelMetadata.model_validate(meta_dict)

        return model, preprocessor, metadata

    def has_artifacts(self) -> bool:
        return self.model_path.exists() and self.preprocessor_path.exists() and self.metadata_path.exists()


registry = ModelRegistry()
model_registry = registry

