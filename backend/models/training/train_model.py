# ============================================================
# models/training/train_model.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Standalone retraining script for the Isolation
#          Forest anomaly detection model.
#
# ── When to Retrain ────────────────────────────────────────
# Run this script to regenerate the model when:
#   • Config hyperparameters change (contamination, estimators,
#     random_state, training_samples).
#   • The feature vector contract changes (new features added
#     or existing ones reordered in anomaly_detector.py).
#   • You want to adjust the synthetic "normal" data ranges
#     (e.g., expanding OCR confidence range, page counts).
#   • The existing .pkl file is missing, corrupt, or you want
#     a fresh baseline before a demo or deployment.
#
# This script is STANDALONE — it is not imported by any other
# module.  The anomaly_detector service has its own auto-train
# fallback, but this script gives explicit control over when
# and how the model is regenerated.
#
# Usage:
#   cd backend/
#   python models/training/train_model.py
#
# Feature Vector Contract (must match anomaly_detector.py):
#   [0] metadata_issue_count    int    (0 for genuine docs)
#   [1] ela_issue_count         int    (0 for genuine docs)
#   [2] ocr_issue_count         int    (0 for genuine docs)
#   [3] template_issue_count    int    (0 for genuine docs)
#   [4] total_text_length       int    (300–8000 range)
#   [5] page_count              int    (1–15 range)
#   [6] mean_ocr_confidence     float  (75.0–99.0 range)
#   [7] ela_suspicious_ratio    float  (0.0–0.05 range)
# ============================================================

from __future__ import annotations

import os
import sys

# ── Ensure the backend/ directory is on sys.path so that
#    `from config import Config` works regardless of the
#    current working directory when invoking this script.
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


# ── Logging ──────────────────────────────────────────────────


def _log(message: str) -> None:
    """Print a tagged log line to the console."""
    print(f"[AuthentIfy] {message}")


# ── Synthetic Data Generation ────────────────────────────────


def _generate_training_data(
    n_samples: int,
    random_state: int,
) -> np.ndarray:
    """Generate synthetic feature vectors for genuine documents.

    Genuine documents share these characteristics:
      • Zero issues across all forensic modules (metadata,
        ELA, OCR, template) — clean docs have nothing flagged.
      • Text length varies by document type and page count
        but falls within a typical 300–8000 character range.
      • Page count ranges from 1 (single-page ID cards) to
        15 (multi-page reports / marksheets).
      • OCR confidence is high (75–99%) because genuine scans
        and digitally rendered PDFs produce clear text.
      • ELA suspicious ratio is very low (0–5%) because no
        content has been spliced or composited.

    The Isolation Forest learns this "normal" distribution
    and flags anything that deviates — documents with issues,
    unusual text volume, or abnormal confidence levels.

    Args:
        n_samples:    Number of training samples to generate.
        random_state: Seed for reproducibility.

    Returns:
        np.ndarray of shape (n_samples, 8) with float64 dtype.
    """
    rng = np.random.RandomState(random_state)

    # [0–3] Issue counts: genuine docs have zero issues
    metadata_issues = np.zeros(n_samples)
    ela_issues = np.zeros(n_samples)
    ocr_issues = np.zeros(n_samples)
    template_issues = np.zeros(n_samples)

    # [4] Text length: varies by doc type and page count
    text_length = rng.randint(300, 8001, size=n_samples)

    # [5] Page count: 1-page IDs to 15-page reports
    page_count = rng.randint(1, 16, size=n_samples)

    # [6] OCR confidence: genuine scans score 75–99%
    mean_confidence = rng.uniform(75.0, 99.0, size=n_samples)

    # [7] ELA suspicious ratio: genuine docs are 0–5%
    ela_ratio = rng.uniform(0.0, 0.05, size=n_samples)

    # Stack into (n_samples, 8) training matrix
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


# ── Training Pipeline ────────────────────────────────────────


def train() -> None:
    """Train and save the Isolation Forest model.

    Generates synthetic training data, fits the model using
    Config hyperparameters, and serializes to Config.MODEL_PATH.
    """
    n_samples = Config.ML_TRAINING_SAMPLES
    n_features = 8

    _log("Training Isolation Forest...")
    _log(f"Samples: {n_samples}")
    _log(f"Features: {n_features}")

    # ── Generate synthetic "normal" document data ────────────
    training_data = _generate_training_data(
        n_samples=n_samples,
        random_state=Config.ML_RANDOM_STATE,
    )

    # ── Train the model ──────────────────────────────────────
    model = IsolationForest(
        contamination=Config.ML_CONTAMINATION,
        n_estimators=Config.ML_N_ESTIMATORS,
        random_state=Config.ML_RANDOM_STATE,
    )
    model.fit(training_data)

    # ── Save to disk ─────────────────────────────────────────
    model_path = Config.MODEL_PATH
    model_dir = os.path.dirname(model_path)

    if model_dir:
        os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, model_path)

    _log(f"Model saved to: {model_path}")
    _log("Training complete.")


# ── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    train()
