from __future__ import annotations
from config import Config

def _get_issues(result: dict) -> list[str]:
    
    if result is None:
        return []
    issues = result.get("issues", [])
    if not isinstance(issues, list):
        return []
    return issues

def _get_anomaly_flag(anomaly_result: dict) -> bool:
    
    if anomaly_result is None:
        return False
    return bool(anomaly_result.get("is_anomaly", False))


def _get_anomaly_confidence(anomaly_result: dict) -> float:
    
    if anomaly_result is None:
        return 50.0
    conf = anomaly_result.get("confidence", 50.0)
    try:
        return float(conf)
    except (TypeError, ValueError):
        return 50.0

def _compute_deductions(
    metadata_issues: list[str],
    ela_issues: list[str],
    ocr_issues: list[str],
    template_issues: list[str],
    is_anomaly: bool,
) -> dict:
    
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

def _determine_verdict(score: int) -> str:
    
    if score >= Config.SCORE_GENUINE_MIN:
        return Config.VERDICT_GENUINE
    if score >= Config.SCORE_SUSPICIOUS_MIN:
        return Config.VERDICT_SUSPICIOUS
    return Config.VERDICT_TAMPERED

def _blend_confidence(
    score: int,
    anomaly_confidence: float,
) -> float:
    
    blended = (score * 0.6) + (anomaly_confidence * 0.4)
    blended = max(0.0, min(100.0, blended))
    return round(blended, 1)

def _generate_summary(
    verdict: str,
    score: int,
    confidence: float,
    total_issues: int,
) -> str:
    
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

    return (
        f"Document shows strong signs of tampering across "
        f"{total_issues} detected issues "
        f"(score: {score}/100)."
    )

def aggregate_scores(
    metadata_result: dict,
    ela_result: dict,
    ocr_result: dict,
    template_result: dict,
    anomaly_result: dict,
) -> dict:
    
    try:
        metadata_issues = _get_issues(metadata_result)
        ela_issues = _get_issues(ela_result)
        ocr_issues = _get_issues(ocr_result)
        template_issues = _get_issues(template_result)
        is_anomaly = _get_anomaly_flag(anomaly_result)
        anomaly_confidence = _get_anomaly_confidence(
            anomaly_result
        )

        deductions = _compute_deductions(
            metadata_issues,
            ela_issues,
            ocr_issues,
            template_issues,
            is_anomaly,
        )

        starting_score = 100

        total_deduction = (
            deductions["metadata_deduction"]
            + deductions["ela_deduction"]
            + deductions["ocr_deduction"]
            + deductions["template_deduction"]
            + deductions["ml_deduction"]
        )

        final_score = max(0, starting_score - total_deduction)
        verdict = _determine_verdict(final_score)
        confidence = _blend_confidence(
            final_score, anomaly_confidence
        )

        reasons: list[str] = []
        reasons.extend(metadata_issues)
        reasons.extend(ela_issues)
        reasons.extend(ocr_issues)
        reasons.extend(template_issues)

        if is_anomaly:
            anomaly_issues = _get_issues(anomaly_result)
            reasons.extend(anomaly_issues)

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
