# ============================================================
# services/anomaly_detector.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Runs ML-based anomaly detection using an Isolation
#          Forest model trained on synthetic "normal" document
#          feature vectors.
#
# ── How It Works ───────────────────────────────────────────
# The Isolation Forest is an unsupervised anomaly detection
# algorithm that works by randomly partitioning data.
# Anomalies — data points that differ from normal — require
# fewer random splits to isolate, so they have shorter
# average path lengths in the forest.
#
# This module:
#   1. Extracts an 8-dimensional feature vector from the
#      upstream service results (metadata, ELA, OCR, template).
#   2. Loads a pre-trained Isolation Forest from disk, or
#      auto-trains one on synthetic "normal" data if no
#      saved model exists.
#   3. Runs prediction: the model flags documents whose
#      feature profile deviates from normal patterns.
#   4. Normalizes the raw decision score to a 0–100
#      confidence value for human consumption.
#
# Called by: routes/analyze.py (Phase 5)
# Inputs  : Result dicts from all 4 upstream services +
#            model file path
# Config  : ML_CONTAMINATION, ML_N_ESTIMATORS,
#            ML_RANDOM_STATE, ML_TRAINING_SAMPLES
# ============================================================

from __future__ import annotations

import os

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from config import Config


# ── Feature Vector Contract ──────────────────────────────────
# The feature vector has exactly 8 elements in this order.
# This is the contract between feature extraction and model
# training — changing the order or count breaks saved models.
#
# Index  Feature                  Type   Source
# ─────  ───────────────────────  ─────  ────────────────────
#   [0]  metadata_issue_count     int    metadata_result
#   [1]  ela_issue_count          int    ela_result
#   [2]  ocr_issue_count          int    ocr_result
#   [3]  template_issue_count     int    template_result
#   [4]  total_text_length        int    ocr_result
#   [5]  page_count               int    ela_result
#   [6]  mean_ocr_confidence      float  ocr_result
#   [7]  ela_suspicious_ratio     float  ela_result (per_page_ela)

_NUM_FEATURES = 8


def build_feature_vector(
    metadata_result: dict,
    ela_result: dict,
    ocr_result: dict,
    template_result: dict,
) -> np.ndarray:
    """Extract and assemble the feature vector from service results.

    Pulls specific numeric values from each upstream service's
    result dict and packs them into a (1, 8) NumPy array
    suitable for Isolation Forest prediction.

    All dictionary accesses use .get() with safe defaults so
    this function never crashes on missing or malformed input.

    Feature vector layout (8 dimensions):
        [0] metadata_issue_count  — Number of metadata issues
        [1] ela_issue_count       — Number of ELA/vision issues
        [2] ocr_issue_count       — Number of OCR issues
        [3] template_issue_count  — Number of template issues
        [4] total_text_length     — Total OCR text characters
        [5] page_count            — Number of PDF pages rendered
        [6] mean_ocr_confidence   — Mean Tesseract confidence
        [7] ela_suspicious_ratio  — Avg suspicious block ratio
            across all pages (from per_page_ela results)

    Args:
        metadata_result: dict from services/metadata_analyzer.py
        ela_result:      dict from services/ela_analyzer.py
        ocr_result:      dict from services/ocr_extractor.py
        template_result: dict from services/template_matcher.py

    Returns:
        np.ndarray of shape (1, 8) with float64 dtype.
    """
    # ── Safe extraction helpers ──────────────────────────────
    meta = metadata_result or {}
    ela = ela_result or {}
    ocr = ocr_result or {}
    tmpl = template_result or {}

    # [0] metadata issue count
    metadata_issues = _safe_int(meta.get("issue_count", 0))

    # [1] ELA / vision issue count
    ela_issues = _safe_int(ela.get("issue_count", 0))

    # [2] OCR issue count
    ocr_issues = _safe_int(ocr.get("issue_count", 0))

    # [3] template issue count
    template_issues = _safe_int(tmpl.get("issue_count", 0))

    # [4] total text length from OCR
    text_length = _safe_int(ocr.get("total_text_length", 0))

    # [5] page count from ELA/vision
    page_count = _safe_int(ela.get("page_count", 0))

    # [6] mean OCR confidence
    mean_conf = _safe_float(ocr.get("mean_confidence", 0.0))

    # [7] ELA suspicious ratio — average across all pages
    # per_page_ela is a list of dicts, each with
    # "suspicious_ratio".  Compute the average; default 0.0.
    ela_ratio = _extract_avg_suspicious_ratio(ela)

    # ── Assemble into (1, 8) array ───────────────────────────
    features = np.array(
        [[
            metadata_issues,
            ela_issues,
            ocr_issues,
            template_issues,
            text_length,
            page_count,
            mean_conf,
            ela_ratio,
        ]],
        dtype=np.float64,
    )

    return features


def load_or_train_model(model_path: str) -> IsolationForest:
    """Load a saved Isolation Forest model, or train a new one.

    If a serialized model exists at model_path, it is loaded
    with joblib.  Otherwise, a new model is trained on
    synthetic "normal" document data that represents what
    clean, genuine documents look like, then saved to disk
    for future use.

    Synthetic training data rationale:
        Genuine documents have zero issues across all forensic
        modules.  Their text length, page count, and OCR
        confidence vary within known ranges.  The model learns
        this "normal" distribution and flags anything that
        deviates — documents with issues, unusual text volume,
        or abnormal confidence levels.

    Args:
        model_path: File path for the serialized model
            (.pkl file).  Created if it does not exist.

    Returns:
        A fitted IsolationForest instance ready for prediction.
    """
    # ── Try loading existing model ───────────────────────────
    if os.path.isfile(model_path):
        model = joblib.load(model_path)
        return model

    # ── Generate synthetic "normal" training data ────────────
    rng = np.random.RandomState(Config.ML_RANDOM_STATE)
    n_samples = Config.ML_TRAINING_SAMPLES

    # Genuine docs have zero issues across all modules
    metadata_issues = np.zeros(n_samples)
    ela_issues = np.zeros(n_samples)
    ocr_issues = np.zeros(n_samples)
    template_issues = np.zeros(n_samples)

    # Text length varies by document type and page count
    text_length = rng.randint(300, 8001, size=n_samples)

    # Page count: most docs are 1–15 pages
    page_count = rng.randint(1, 16, size=n_samples)

    # OCR confidence: genuine scans/renders score 75–99%
    mean_confidence = rng.uniform(75.0, 99.0, size=n_samples)

    # ELA suspicious ratio: genuine docs have very low ratios
    ela_ratio = rng.uniform(0.0, 0.05, size=n_samples)

    # Stack into (n_samples, 8) training matrix
    training_data = np.column_stack([
        metadata_issues,
        ela_issues,
        ocr_issues,
        template_issues,
        text_length,
        page_count,
        mean_confidence,
        ela_ratio,
    ])

    # ── Train Isolation Forest ───────────────────────────────
    model = IsolationForest(
        contamination=Config.ML_CONTAMINATION,
        n_estimators=Config.ML_N_ESTIMATORS,
        random_state=Config.ML_RANDOM_STATE,
    )
    model.fit(training_data)

    # ── Save to disk for future runs ─────────────────────────
    # Ensure the parent directory exists
    model_dir = os.path.dirname(model_path)
    if model_dir:
        os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, model_path)

    return model


def run_anomaly_detection(
    metadata_result: dict,
    ela_result: dict,
    ocr_result: dict,
    template_result: dict,
    model_path: str,
) -> dict:
    """Run ML anomaly detection on aggregated analysis features.

    Orchestrates the full anomaly detection pipeline:
        1. Build the 8-dimensional feature vector from all
           upstream service results.
        2. Load the Isolation Forest model (or auto-train if
           no saved model exists).
        3. Run prediction and decision_function scoring.
        4. Normalize the raw score to a 0–100 confidence.
        5. Return structured result with transparency data.

    Confidence normalization:
        The Isolation Forest's decision_function() returns a
        raw float where:
          • Positive values → normal (higher = more normal)
          • Negative values → anomaly (lower = more anomalous)
        Typical range is roughly [-0.5, 0.5].  We clip to
        this range, shift by +0.5, and scale to [0, 100]:
            normalized = (clip(raw, -0.5, 0.5) + 0.5) * 100
        So 0 = strongly anomalous, 100 = strongly normal.

    Args:
        metadata_result: dict from services/metadata_analyzer.py
        ela_result:      dict from services/ela_analyzer.py
        ocr_result:      dict from services/ocr_extractor.py
        template_result: dict from services/template_matcher.py
        model_path:      Path to serialized IsolationForest model.

    Returns:
        dict with keys:
            is_anomaly     (bool)       — True if the model
                flags this document as anomalous.
            confidence     (float)      — 0–100, higher means
                more confident the doc is genuine.
            raw_score      (float)      — Raw decision_function
                output (for debugging / transparency).
            feature_vector (list[float]) — The 8 features used
                (for debugging / transparency).
            issues         (list[str])  — Human-readable issues
                if anomaly detected.
            error          (None|str)   — Error description on
                failure; None on success.
    """
    try:
        # ── Step 1: Build feature vector ─────────────────────
        features = build_feature_vector(
            metadata_result,
            ela_result,
            ocr_result,
            template_result,
        )

        # ── Step 2: Load or train model ──────────────────────
        model = load_or_train_model(model_path)

        # ── Step 3: Predict and score ────────────────────────
        # predict() returns +1 (normal) or -1 (anomaly)
        prediction = model.predict(features)[0]
        is_anomaly = prediction == -1

        # decision_function() returns the raw anomaly score.
        # Positive = normal, negative = anomaly.
        raw_score = float(model.decision_function(features)[0])

        # ── Step 4: Normalize to 0–100 confidence ────────────
        # Raw decision_function output typically ranges from
        # about -0.5 (strong anomaly) to +0.5 (strongly
        # normal).  Clip to this range, shift by +0.5 to get
        # [0, 1], then scale to [0, 100].
        #
        # Result: 0 = highly anomalous, 100 = highly normal.
        confidence = float(
            (np.clip(raw_score, -0.5, 0.5) + 0.5) * 100
        )
        confidence = round(confidence, 1)

        # ── Step 5: Build issues list ────────────────────────
        issues: list[str] = []
        if is_anomaly:
            issues.append(
                "ML anomaly detector flagged this document's "
                "feature profile as deviating significantly "
                "from genuine document patterns."
            )

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "raw_score": round(raw_score, 6),
            "feature_vector": features[0].tolist(),
            "issues": issues,
            "error": None,
        }

    except Exception as exc:
        # Never crash — return safe neutral result
        return {
            "is_anomaly": False,
            "confidence": 50.0,
            "raw_score": 0.0,
            "feature_vector": [],
            "issues": [],
            "error": f"Anomaly detection failed: {exc}",
        }


# ── Internal Helpers ─────────────────────────────────────────


def _safe_int(value) -> int:
    """Convert a value to int, defaulting to 0 on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value) -> float:
    """Convert a value to float, defaulting to 0.0 on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_avg_suspicious_ratio(
    ela_result: dict,
) -> float:
    """Extract the average ELA suspicious ratio across pages.

    Reads per_page_ela from the ELA result and averages the
    suspicious_ratio values.  If no valid data is available,
    returns 0.0.

    Args:
        ela_result: dict from services/ela_analyzer.py
            containing "per_page_ela" (list of dicts).

    Returns:
        Average suspicious_ratio as float (0.0–1.0).
    """
    per_page = ela_result.get("per_page_ela", [])

    if not per_page or not isinstance(per_page, list):
        return 0.0

    ratios: list[float] = []

    for page_ela in per_page:
        if page_ela is None or not isinstance(page_ela, dict):
            continue

        ratio = page_ela.get("suspicious_ratio")
        if ratio is not None:
            try:
                ratios.append(float(ratio))
            except (TypeError, ValueError):
                continue

    if not ratios:
        return 0.0

    return sum(ratios) / len(ratios)
