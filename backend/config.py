import os

class Config:
  
    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )
    
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR, "uploads"
    )

    PROCESSED_FOLDER = os.path.join(
        BASE_DIR, "processed"
    )

    MODEL_FOLDER = os.path.join(
        BASE_DIR, "models"
    )

    MODEL_PATH = os.path.join(
        BASE_DIR, "models", "isolation_forest.pkl"
    )

    REPORTS_FOLDER = os.path.join(
        BASE_DIR, "reports"
    )
    
    TEMPLATES_FOLDER = os.path.join(
        BASE_DIR, "templates"
    )

    ALLOWED_EXTENSIONS = {
        "pdf"
    }

    MAX_FILE_SIZE_MB = 25

    MAX_FILE_SIZE_BYTES = (
        MAX_FILE_SIZE_MB * 1024 * 1024
    )

    DEBUG = True
    PORT = 5000
    HOST = "0.0.0.0"

    DEDUCT_METADATA_ISSUE = 25
    DEDUCT_VISION_ISSUE = 15
    DEDUCT_OCR_ISSUE = 20
    DEDUCT_ML_ANOMALY = 15
    SCORE_GENUINE_MIN = 80
    SCORE_SUSPICIOUS_MIN = 50
    VERDICT_GENUINE = "Genuine"
    VERDICT_SUSPICIOUS = "Suspicious"
    VERDICT_TAMPERED = "Tampered"
    BLUR_THRESHOLD = 100.0
    NOISE_VARIANCE_THRESHOLD = 25.0
    DARK_REGION_THRESHOLD = 40
    
    MIN_TEXT_LENGTH = 50
    MIN_OCR_CONFIDENCE = 60
    GARBLE_RATIO_THRESHOLD = 0.4
    
    ML_CONTAMINATION = 0.1
    ML_N_ESTIMATORS = 100
    ML_RANDOM_STATE = 42
    ML_TRAINING_SAMPLES = 500

    SUSPICIOUS_PRODUCERS = [
        "iLovePDF",
        "SmallPDF",
        "Sejda",
        "PDF24",
        "PDFescape",
        "Online2PDF",
        "CutePDF",
        "doPDF",
        "Nitro PDF",
        "PDFsam",
        "Unknown",
    ]

    SUSPICIOUS_CREATORS = [
        "Online PDF Editor",
        "PDF Candy",
        "Canva",
        "Google Docs",
        "WPS Office",
        "LibreOffice",
        "Foxit PhantomPDF",
        "Master PDF Editor",
        "PDF-XChange Editor",
        "Unknown",
    ]
