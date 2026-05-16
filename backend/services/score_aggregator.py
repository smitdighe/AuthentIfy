# ============================================================
# services/score_aggregator.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Final aggregation layer — combines signals from all
#          forensic analysis services into a single explainable
#          score, verdict, and confidence value.
#
# This is PURE LOGIC — no algorithms, no file I/O, no ML,
# no external dependencies. Only scoring math and response
# assembly.
#
# Called by: routes/analyze.py (final step before response)
# Inputs  : Result dicts from metadata_analyzer, ela_analyzer,
#           ocr_extractor, template_matcher, ml_anomaly_detector
# Config  : All DEDUCT_ constants, SCORE_ thresholds,
#           VERDICT_ strings
# ============================================================

from __future__ import annotations

from config import Config


# ── Safe Result Access ───────────────────────────────────────


def _get_issues(result: dict) -> list[str]:
    """Safely extract the issues list from a service result.

    Guards against None results, missing keys, and non-list
    values so the aggregator never crashes on malformed input.

    Args:
        result: A service result dict (may be None).

    Returns:
        list[str] of issues, empty list on any failure.
    """
    if result is None:
        return []

    issues = result.get("issues", [])

    if not isinstance(issues, list):
        return []

    return issues


def _get_anomaly_flag(anomaly_result: dict) -> bool:
    """Safely extract the is_anomaly flag from ML result.

    Args:
        anomaly_result: ML anomaly detector result dict.

    Returns:
        True if the document was flagged as an anomaly.
    """
    if anomaly_result is None:
        return False

    return bool(anomaly_result.get("is_anomaly", False))


def _get_anomaly_confidence(anomaly_result: dict) -> float:
    """Safely extract ML confidence from anomaly result.

    Args:
        anomaly_result: ML anomaly detector result dict.

    Returns:
        Confidence value (0.0–100.0), defaults to 50.0
        (neutral) if unavailable.
    """
    if anomaly_result is None:
        return 50.0

    conf = anomaly_result.get("confidence", 50.0)

    try:
        return float(conf)
    except (TypeError, ValueError):
        return 50.0


# ── Deduction Calculation ────────────────────────────────────


def _compute_deductions(
    metadata_issues: list[str],
    ela_issues: list[str],
    ocr_issues: list[str],
    template_issues: list[str],
    is_anomaly: bool,
) -> dict:
    """Compute per-module score deductions.

    Each issue in a module's list incurs its configured penalty.
    The ML anomaly flag is a flat one-time deduction.

    Args:
        metadata_issues:  Issues from metadata_analyzer.
        ela_issues:       Issues from ela_analyzer.
        ocr_issues:       Issues from ocr_extractor.
        template_issues:  Issues from template_matcher.
        is_anomaly:       True if ML flagged as anomaly.

    Returns:
        dict with per-module deduction values and totals.
    """
    meta_ded = len(metadata_issues) * Config.DEDUCT_METADATA_ISSUE
    ela_ded = len(ela_issues) * Config.DEDUCT_VISION_ISSUE
    ocr_ded = len(ocr_issues) * Config.DEDUCT_OCR_ISSUE
    tmpl_ded = (
        len(template_issues) * Config.DEDUCT_METADATA_ISSUE
    )
    ml_ded = Config.DEDUCT_ML_ANOMALY if is_anomaly else 0

    return {
        "metadata_deduction": meta_ded,
        "ela_deduction": ela_ded,
        "ocr_deduction": ocr_ded,
        "template_deduction": tmpl_ded,
        "ml_deduction": ml_ded,
    }


# ── Verdict Determination ────────────────────────────────────


def _determine_verdict(score: int) -> str:
    """Map a numeric score to a verdict label.

    Score ranges (from Config):
        100–80  → Genuine
         79–50  → Suspicious
         49– 0  → Tampered

    Args:
        score: Final clamped score (0–100).

    Returns:
        Verdict string from Config.
    """
    if score >= Config.SCORE_GENUINE_MIN:
        return Config.VERDICT_GENUINE

    if score >= Config.SCORE_SUSPICIOUS_MIN:
        return Config.VERDICT_SUSPICIOUS

    return Config.VERDICT_TAMPERED


# ── Confidence Blending ──────────────────────────────────────


def _blend_confidence(
    score: int,
    anomaly_confidence: float,
) -> float:
    """Blend the document score with ML confidence.

    Formula:
        confidence = (score × 0.6) + (anomaly_confidence × 0.4)

    This weights the rule-based score slightly higher than
    the ML signal, reflecting that metadata/vision/OCR checks
    are more interpretable and auditable.

    Args:
        score:              Final clamped score (0–100).
        anomaly_confidence: ML model confidence (0.0–100.0).

    Returns:
        Blended confidence rounded to 1 decimal (0.0–100.0).
    """
    blended = (score * 0.6) + (anomaly_confidence * 0.4)

    # Clamp to valid range
    blended = max(0.0, min(100.0, blended))

    return round(blended, 1)


# ── Summary Generation ───────────────────────────────────────


def _generate_summary(
    verdict: str,
    score: int,
    confidence: float,
    total_issues: int,
) -> str:
    """Generate a one-sentence human-readable summary for the UI.

    Uses verdict-specific templates:
        Genuine    → emphasizes authenticity and confidence
        Suspicious → highlights issue count and review need
        Tampered   → warns of strong tampering evidence

    Args:
        verdict:      Verdict string (Genuine/Suspicious/Tampered).
        score:        Final score (0–100).
        confidence:   Blended confidence (0.0–100.0).
        total_issues: Total number of issues across all modules.

    Returns:
        Human-readable summary sentence.
    """
    if verdict == Config.VERDICT_GENUINE:
        return (
            f"Document appears authentic with a score of "
            f"{score}/100 and {confidence}% confidence."
        )

    if verdict == Config.VERDICT_SUSPICIOUS:
        return (
            f"Document shows {total_issues} suspicious "
            f"indicators and requires further review "
            f"(score: {score}/100)."
        )

    # Tampered
    return (
        f"Document shows strong signs of tampering across "
        f"{total_issues} detected issues "
        f"(score: {score}/100)."
    )


# ── Main Aggregation Entry Point ─────────────────────────────


def aggregate_scores(
    metadata_result: dict,
    ela_result: dict,
    ocr_result: dict,
    template_result: dict,
    anomaly_result: dict,
) -> dict:
    """Aggregate all forensic analysis results into a final verdict.

    This is the final decision layer of the AuthentIfy pipeline.
    It combines signals from 5 independent analysis modules into
    a single explainable score, verdict, and confidence value.

    Scoring algorithm:
        1. Start at 100 (perfect score).
        2. Deduct Config.DEDUCT_METADATA_ISSUE per metadata issue.
        3. Deduct Config.DEDUCT_VISION_ISSUE per ELA/vision issue.
        4. Deduct Config.DEDUCT_OCR_ISSUE per OCR issue.
        5. Deduct Config.DEDUCT_METADATA_ISSUE per template issue.
        6. Deduct Config.DEDUCT_ML_ANOMALY if ML flags anomaly.
        7. Floor score at 0 (never negative).
        8. Map score to verdict via Config thresholds.
        9. Blend score with ML confidence for final confidence.

    Args:
        metadata_result: dict from services/metadata_analyzer.py
        ela_result:      dict from services/ela_analyzer.py
        ocr_result:      dict from services/ocr_extractor.py
        template_result: dict from services/template_matcher.py
        anomaly_result:  dict from services/ml_anomaly_detector.py

    Returns:
        dict with keys:
            score       (int)        — 0–100 final score
            verdict     (str)        — Genuine/Suspicious/Tampered
            confidence  (float)      — 0.0–100.0 blended confidence
            reasons     (list[str])  — ALL issues, flat list
            breakdown   (dict)       — Per-module deduction detail
            summary     (str)        — One-sentence UI summary
            error       (None|str)   — Error on total failure
    """
    try:
        # ── Extract issues from each module ──────────────────
        metadata_issues = _get_issues(metadata_result)
        ela_issues = _get_issues(ela_result)
        ocr_issues = _get_issues(ocr_result)
        template_issues = _get_issues(template_result)
        is_anomaly = _get_anomaly_flag(anomaly_result)
        anomaly_confidence = _get_anomaly_confidence(
            anomaly_result
        )

        # ── Compute deductions ───────────────────────────────
        deductions = _compute_deductions(
            metadata_issues,
            ela_issues,
            ocr_issues,
            template_issues,
            is_anomaly,
        )

        # ── Apply deductions to starting score ───────────────
        starting_score = 100

        total_deduction = (
            deductions["metadata_deduction"]
            + deductions["ela_deduction"]
            + deductions["ocr_deduction"]
            + deductions["template_deduction"]
            + deductions["ml_deduction"]
        )

        # Floor at 0 — score can never go negative
        final_score = max(0, starting_score - total_deduction)

        # ── Determine verdict ────────────────────────────────
        verdict = _determine_verdict(final_score)

        # ── Blend confidence ─────────────────────────────────
        confidence = _blend_confidence(
            final_score, anomaly_confidence
        )

        # ── Collect all reasons (flat list) ──────────────────
        reasons: list[str] = []
        reasons.extend(metadata_issues)
        reasons.extend(ela_issues)
        reasons.extend(ocr_issues)
        reasons.extend(template_issues)

        if is_anomaly:
            anomaly_issues = _get_issues(anomaly_result)
            reasons.extend(anomaly_issues)

        # ── Build breakdown dict ─────────────────────────────
        breakdown = {
            "metadata_deduction": deductions[
                "metadata_deduction"
            ],
            "ela_deduction": deductions["ela_deduction"],
            "ocr_deduction": deductions["ocr_deduction"],
            "template_deduction": deductions[
                "template_deduction"
            ],
            "ml_deduction": deductions["ml_deduction"],
            "starting_score": starting_score,
            "final_score": final_score,
        }

        # ── Generate summary ─────────────────────────────────
        summary = _generate_summary(
            verdict, final_score, confidence, len(reasons)
        )

        return {
            "score": final_score,
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "breakdown": breakdown,
            "summary": summary,
            "error": None,
        }

    except Exception as exc:
        # Total failure — return safe default, never crash
        return {
            "score": 0,
            "verdict": Config.VERDICT_TAMPERED,
            "confidence": 0.0,
            "reasons": [],
            "breakdown": {
                "metadata_deduction": 0,
                "ela_deduction": 0,
                "ocr_deduction": 0,
                "template_deduction": 0,
                "ml_deduction": 0,
                "starting_score": 100,
                "final_score": 0,
            },
            "summary": (
                "Scoring failed — treating as tampered "
                "for safety."
            ),
            "error": f"Score aggregation failed: {exc}",
        }
