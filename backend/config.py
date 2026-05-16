# ============================================================
# config.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Single source of truth for ALL constants, paths,
#          thresholds, and scoring values used across the
#          entire backend pipeline.
#
# WARNING: Do not hardcode any of these values elsewhere.
#          Every module must import from this file:
#              from config import Config
# ============================================================

import os


class Config:
    """
    Central configuration class for the AuthentIfy backend.

    All constants are organized into clearly labeled sections.
    Every value is a class-level attribute — no instance needed.
    Import usage:  from config import Config
    """

    # ── SECTION A: Directory Paths ───────────────────────────
    # All paths are relative to this file's location (backend/)
    # and work on Windows, macOS, and Linux.

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )  # Absolute path to backend/

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR, "uploads"
    )  # Incoming PDF uploads land here

    PROCESSED_FOLDER = os.path.join(
        BASE_DIR, "processed"
    )  # Vision-extracted page images stored here

    MODEL_FOLDER = os.path.join(
        BASE_DIR, "models"
    )  # Trained ML model artifacts

    MODEL_PATH = os.path.join(
        BASE_DIR, "models", "isolation_forest.pkl"
    )  # Serialized IsolationForest model file

    # Folder where JSON verdict reports are persisted per document
    REPORTS_FOLDER = os.path.join(
        BASE_DIR, "reports"
    )

    # Folder containing known authentic document template JSON files
    TEMPLATES_FOLDER = os.path.join(
        BASE_DIR, "templates"
    )

    # ── SECTION B: File Validation ───────────────────────────
    # Controls what the /analyze endpoint will accept.

    ALLOWED_EXTENSIONS = {
        "pdf"
    }  # Only PDF files are accepted for analysis

    MAX_FILE_SIZE_MB = 25  # 25 MB — covers 99% of scanned PDFs while blocking abuse

    MAX_FILE_SIZE_BYTES = (
        MAX_FILE_SIZE_MB * 1024 * 1024
    )  # Derived: 25 MB → 26,214,400 bytes

    # ── SECTION C: Flask Settings ────────────────────────────
    # Runtime configuration for the Flask development server.

    DEBUG = True  # Enabled for hackathon — provides detailed error pages

    PORT = 5000  # Default Flask port; change if conflicts arise

    HOST = "0.0.0.0"  # Bind to all interfaces for LAN/container access

    # ── SECTION D: Scoring — Deduction Values ────────────────
    # Each constant represents the number of points subtracted
    # from a perfect score of 100 when the corresponding issue
    # is detected. Multiple issues of the same type stack.

    DEDUCT_METADATA_ISSUE = 25  # Per metadata red flag (e.g., mismatched dates, suspicious producer)

    DEDUCT_VISION_ISSUE = 15  # Per visual anomaly (e.g., blur, noise spikes, dark patch splicing)

    DEDUCT_OCR_ISSUE = 20  # Per OCR anomaly (e.g., garbled text, abnormally sparse content)

    DEDUCT_ML_ANOMALY = 15  # Flat penalty when IsolationForest flags doc as outlier

    # ── SECTION E: Scoring — Verdict Thresholds ──────────────
    # Score ranges determine the final verdict label:
    #   100–80  → Genuine   (document appears authentic)
    #    79–50  → Suspicious (anomalies found, manual review needed)
    #    49– 0  → Tampered   (strong evidence of manipulation)

    SCORE_GENUINE_MIN = 80  # Score ≥ 80 → classified as Genuine

    SCORE_SUSPICIOUS_MIN = 50  # Score 50–79 → classified as Suspicious

    # Anything below SCORE_SUSPICIOUS_MIN (< 50) → Tampered

    VERDICT_GENUINE = "Genuine"  # Label for authentic documents

    VERDICT_SUSPICIOUS = "Suspicious"  # Label for documents needing review

    VERDICT_TAMPERED = "Tampered"  # Label for manipulated documents

    # ── SECTION F: Vision Analysis Thresholds ────────────────
    # Used by services/vision.py when analyzing page images.

    BLUR_THRESHOLD = 100.0  # Laplacian variance below this → blurry/suspicious (typical sharp docs score 300+)

    NOISE_VARIANCE_THRESHOLD = 25.0  # Pixel std-dev above this in uniform regions → noise inconsistency flag

    DARK_REGION_THRESHOLD = 40  # Pixel intensity (0–255) below this → flagged as dark region / cover-up

    # ── SECTION G: OCR Thresholds ────────────────────────────
    # Used by services/ocr.py when evaluating extracted text.

    MIN_TEXT_LENGTH = 50  # Character count below this → document is suspiciously sparse

    MIN_OCR_CONFIDENCE = 60  # Tesseract mean confidence (0–100) below this → unreliable / manipulated text

    GARBLE_RATIO_THRESHOLD = 0.4  # Ratio of non-alphanumeric chars to total; above this → garbled / obfuscated text

    # ── SECTION H: ML Model Settings ─────────────────────────
    # Hyperparameters for the IsolationForest anomaly detector
    # used in services/ml_model.py.

    ML_CONTAMINATION = 0.1  # Expected fraction of anomalies in training data (valid: 0 < x < 0.5)

    ML_N_ESTIMATORS = 100  # Number of isolation trees in the forest ensemble

    ML_RANDOM_STATE = 42  # Fixed seed for reproducible model training

    ML_TRAINING_SAMPLES = 500  # Number of synthetic "normal" feature vectors to generate for training

    # ── SECTION I: Metadata Suspicious Keywords ──────────────
    # Lists of PDF producer/creator strings that indicate the
    # document may have been altered using online tools or
    # unusual software. Used by services/metadata.py.

    SUSPICIOUS_PRODUCERS = [
        "iLovePDF",  # Popular online PDF editor — often used to alter docs
        "SmallPDF",  # Online conversion/editing tool
        "Sejda",  # Browser-based PDF editor
        "PDF24",  # Free PDF manipulation suite
        "PDFescape",  # Online PDF form filler / editor
        "Online2PDF",  # Web-based converter / merger
        "CutePDF",  # Lightweight PDF writer — limited provenance tracking
        "doPDF",  # Virtual PDF printer with minimal metadata
        "Nitro PDF",  # Sometimes used for quick edits
        "PDFsam",  # PDF split-and-merge utility
        "Unknown",  # Generic fallback — missing producer is a red flag
    ]

    SUSPICIOUS_CREATORS = [
        "Online PDF Editor",  # Generic web-based editor
        "PDF Candy",  # Free online PDF toolkit
        "Canva",  # Design tool — unusual source for formal PDFs
        "Google Docs",  # While legitimate, often used to re-create docs from scratch
        "WPS Office",  # Free office suite with limited integrity features
        "LibreOffice",  # Open-source — not suspicious alone, but flagged for pattern matching
        "Foxit PhantomPDF",  # Advanced editing capabilities
        "Master PDF Editor",  # Full-featured editor — can alter content seamlessly
        "PDF-XChange Editor",  # Editing tool with page manipulation features
        "Unknown",  # Missing creator string is a red flag
    ]


# ============================================================
# SCORING MATH VERIFICATION
# ============================================================
#
# Worst-case simulation:
#   Starting score            = 100
#   − 2 × metadata issues    = 100 − (2 × 25) = 50
#   − 2 × vision issues      =  50 − (2 × 15) = 20
#   − 1 × OCR issue          =  20 − (1 × 20) =  0
#   − 1 × ML anomaly         =   0 − (1 × 15) = −15  (clamped to 0)
#
#   Final score  = 0   (or clamped to 0 if scoring.py floors at 0)
#   Verdict      = Tampered  (0 < 50 ✓)
#
# Moderate-case simulation:
#   Starting score            = 100
#   − 1 × metadata issue     = 100 − 25 = 75
#   − 1 × vision issue       =  75 − 15 = 60
#
#   Final score  = 60
#   Verdict      = Suspicious  (50 ≤ 60 < 80 ✓)
#
# Clean document:
#   Starting score            = 100
#   No deductions applied.
#
#   Final score  = 100
#   Verdict      = Genuine  (100 ≥ 80 ✓)
#
# ✓ Worst case lands at 0 — well below 50 (Tampered)
# ✓ Moderate case lands in Suspicious range
# ✓ Clean case lands in Genuine range
# ✓ All three verdict bands (Genuine / Suspicious / Tampered)
#   are reachable and mutually exclusive.
# ============================================================
