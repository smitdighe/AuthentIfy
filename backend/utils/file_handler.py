import json
import os
import uuid

from werkzeug.utils import secure_filename
from config import Config

def validate_extension(filename: str) -> bool:
    
    if not filename or not isinstance(filename, str):
        return False
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in Config.ALLOWED_EXTENSIONS

def validate_file_size(file_path: str) -> tuple[bool, str]:
    
    try:
        size_bytes = os.path.getsize(file_path)
    except (OSError, TypeError):
        return False, "Unable to determine file size."

    if size_bytes <= Config.MAX_FILE_SIZE_BYTES:
        return True, ""

    size_mb = size_bytes / (1024 * 1024)
    limit_mb = Config.MAX_FILE_SIZE_MB
    reason = (
        f"File is {size_mb:.1f} MB. "
        f"Maximum allowed is {limit_mb} MB."
    )
    return False, reason

def sanitize_filename(filename: str) -> tuple[str, str]:
    
    report_id = uuid.uuid4().hex
    safe_name = secure_filename(filename) if filename else ""

    if not safe_name:
        safe_name = "document.pdf"

    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"

    unique_name = f"{report_id}_{safe_name}"
    return unique_name, report_id

def save_upload(
    file_object, original_filename: str
) -> tuple[bool, str, str]:
    
    try:
        safe_name, report_id = sanitize_filename(original_filename)

        if not ensure_directory(Config.UPLOAD_FOLDER):
            return False, "Could not create upload directory.", ""

        saved_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
        file_object.save(saved_path)

        return True, saved_path, report_id

    except OSError as exc:
        return False, f"Disk write failed: {exc}", ""
    except AttributeError:
        return False, "Invalid file object received.", ""


def delete_upload(file_path: str) -> bool:
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            return True
        return False
    except OSError:
        return False

def ensure_directory(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False

def save_report(report_id: str, report_data: dict) -> bool:
    
    try:
        if not ensure_directory(Config.REPORTS_FOLDER):
            return False

        report_path = os.path.join(
            Config.REPORTS_FOLDER, f"{report_id}.json"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        return True

    except (OSError, TypeError, ValueError):
        return False


def load_report(report_id: str) -> tuple[bool, dict]:
    
    report_path = os.path.join(
        Config.REPORTS_FOLDER, f"{report_id}.json"
    )

    if not os.path.isfile(report_path):
        return False, {}
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return True, data
    except (OSError, json.JSONDecodeError):
        return False, {}
