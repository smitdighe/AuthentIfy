from __future__ import annotations

import os

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from config import Config

_NUM_FEATURES = 8

def build_feature_vector(
    metadata_result: dict,
    ela_result: dict,
    ocr_result: dict,
    template_result: dict,
) -> np.ndarray:
    
    meta = metadata_result or {}
    ela = ela_result or {}
    ocr = ocr_result or {}
    tmpl = template_result or {}

    metadata_issues = _safe_int(meta.get("issue_count", 0))
    ela_issues = _safe_int(ela.get("issue_count", 0))
    ocr_issues = _safe_int(ocr.get("issue_count", 0))
    template_issues = _safe_int(tmpl.get("issue_count", 0))
    text_length = _safe_int(ocr.get("total_text_length", 0))
    page_count = _safe_int(ela.get("page_count", 0))
    mean_conf = _safe_float(ocr.get("mean_confidence", 0.0))
    ela_ratio = _extract_avg_suspicious_ratio(ela)

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
    
    if os.path.isfile(model_path):
        model = joblib.load(model_path)
        return model

    rng = np.random.RandomState(Config.ML_RANDOM_STATE)
    n_samples = Config.ML_TRAINING_SAMPLES

    metadata_issues = np.zeros(n_samples)
    ela_issues = np.zeros(n_samples)
    ocr_issues = np.zeros(n_samples)
    template_issues = np.zeros(n_samples)

    text_length = rng.randint(300, 8001, size=n_samples)
    page_count = rng.randint(1, 16, size=n_samples)
    mean_confidence = rng.uniform(75.0, 99.0, size=n_samples)
    ela_ratio = rng.uniform(0.0, 0.05, size=n_samples)

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

    model = IsolationForest(
        contamination=Config.ML_CONTAMINATION,
        n_estimators=Config.ML_N_ESTIMATORS,
        random_state=Config.ML_RANDOM_STATE,
    )
    model.fit(training_data)

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
    
    try:
        features = build_feature_vector(
            metadata_result,
            ela_result,
            ocr_result,
            template_result,
        )

        model = load_or_train_model(model_path)

        prediction = model.predict(features)[0]
        is_anomaly = bool(prediction == -1)
        raw_score = float(model.decision_function(features)[0])

        confidence = float(
            (np.clip(raw_score, -0.5, 0.5) + 0.5) * 100
        )
        confidence = round(confidence, 1)

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
        return {
            "is_anomaly": False,
            "confidence": 50.0,
            "raw_score": 0.0,
            "feature_vector": [],
            "issues": [],
            "error": f"Anomaly detection failed: {exc}",
        }

def _safe_int(value) -> int:
    
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value) -> float:
    
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_avg_suspicious_ratio(
    ela_result: dict,
) -> float:
    
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
