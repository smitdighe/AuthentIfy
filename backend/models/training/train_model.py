from __future__ import annotations

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.abspath(
    os.path.join(_SCRIPT_DIR, os.pardir, os.pardir)
)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from config import Config

def _log(message: str) -> None:
    print(f"[AuthentIfy] {message}")

def _generate_training_data(
    n_samples: int,
    random_state: int,
) -> np.ndarray:
    
    rng = np.random.RandomState(random_state)

    metadata_issues = np.zeros(n_samples)
    ela_issues = np.zeros(n_samples)
    ocr_issues = np.zeros(n_samples)
    template_issues = np.zeros(n_samples)
    text_length = rng.randint(300, 8001, size=n_samples)
    page_count = rng.randint(1, 16, size=n_samples)
    mean_confidence = rng.uniform(75.0, 99.0, size=n_samples)
    ela_ratio = rng.uniform(0.0, 0.05, size=n_samples)

    return np.column_stack([
        metadata_issues,
        ela_issues,
        ocr_issues,
        template_issues,
        text_length,
        page_count,
        mean_confidence,
        ela_ratio,
    ])

def train() -> None:
    n_samples = Config.ML_TRAINING_SAMPLES
    n_features = 8

    _log("Training Isolation Forest...")
    _log(f"Samples: {n_samples}")
    _log(f"Features: {n_features}")

    training_data = _generate_training_data(
        n_samples=n_samples,
        random_state=Config.ML_RANDOM_STATE,
    )
    
    model = IsolationForest(
        contamination=Config.ML_CONTAMINATION,
        n_estimators=Config.ML_N_ESTIMATORS,
        random_state=Config.ML_RANDOM_STATE,
    )
    model.fit(training_data)

    model_path = Config.MODEL_PATH
    model_dir = os.path.dirname(model_path)

    if model_dir:
        os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, model_path)

    _log(f"Model saved to: {model_path}")
    _log("Training complete.")

if __name__ == "__main__":
    train()
