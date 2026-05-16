# ============================================================
# utils/file_handler.py — AuthentIfy Backend
# Project: AuthentIfy — "Verify before you trust."
# Role   : Secure file validation, storage, and retrieval
#          utilities used across the backend pipeline.
#
# This is a PURE utility module — no Flask routes, no analysis
# logic. Only filesystem operations and input validation.
#
# Consumers: routes/analyze.py, routes/report.py
# ============================================================

import json
import os
import uuid

from werkzeug.utils import secure_filename

from config import Config


# ── Extension Validation ─────────────────────────────────────


def validate_extension(filename: str) -> bool:
    """Check whether the file has an allowed extension.

    Performs a case-insensitive comparison against
    Config.ALLOWED_EXTENSIONS.

    Args:
        filename: Original filename from the upload request.

    Returns:
        True if the extension is allowed, False otherwise.
        Returns False for None, empty string, or missing extension.
    """
    if not filename or not isinstance(filename, str):
        return False

    # Split on the last dot — handles names like "report.v2.pdf"
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in Config.ALLOWED_EXTENSIONS


# ── File Size Validation ─────────────────────────────────────


def validate_file_size(file_path: str) -> tuple[bool, str]:
    """Verify that a saved file does not exceed the size limit.

    Args:
        file_path: Absolute path to the file on disk.

    Returns:
        (True, "")  if the file is within the allowed size.
        (False, human_readable_reason) if the file is too large
        or the path is unreadable.
    """
    try:
        size_bytes = os.path.getsize(file_path)
    except (OSError, TypeError):
        return False, "Unable to determine file size."

    if size_bytes <= Config.MAX_FILE_SIZE_BYTES:
        return True, ""

    # Build a human-readable message with 1-decimal MB values
    size_mb = size_bytes / (1024 * 1024)
    limit_mb = Config.MAX_FILE_SIZE_MB
    reason = (
        f"File is {size_mb:.1f} MB. "
        f"Maximum allowed is {limit_mb} MB."
    )
    return False, reason


# ── Filename Sanitization ────────────────────────────────────


def sanitize_filename(filename: str) -> tuple[str, str]:
    """Sanitize an uploaded filename and prepend a unique ID.

    Uses werkzeug's secure_filename to strip path traversal
    characters, then prepends a UUID4 to guarantee uniqueness.

    Args:
        filename: Original filename from the upload request.

    Returns:
        (safe_filename, report_id) where:
        - safe_filename has the format "{uuid}_{sanitized}.pdf"
        - report_id is the UUID string (reused for report saving)
    """
    report_id = uuid.uuid4().hex  # 32-char hex string, no dashes

    safe_name = secure_filename(filename) if filename else ""

    # Fallback if secure_filename strips everything (e.g., "../")
    if not safe_name:
        safe_name = "document.pdf"

    # Ensure .pdf extension survives sanitization
    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"

    unique_name = f"{report_id}_{safe_name}"
    return unique_name, report_id


# ── Upload Save / Delete ─────────────────────────────────────


def save_upload(
    file_object, original_filename: str
) -> tuple[bool, str, str]:
    """Save an uploaded file to the uploads directory.

    Sanitizes the filename, ensures the upload folder exists,
    and writes the file to disk.

    Args:
        file_object: A Flask FileStorage object (has a .save method).
        original_filename: The user-provided filename.

    Returns:
        (True,  saved_file_path, report_id) on success.
        (False, error_message,   "")         on failure.
    """
    try:
        safe_name, report_id = sanitize_filename(original_filename)

        # Guarantee the upload directory exists
        if not ensure_directory(Config.UPLOAD_FOLDER):
            return False, "Could not create upload directory.", ""

        saved_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
        file_object.save(saved_path)

        return True, saved_path, report_id

    except OSError as exc:
        return False, f"Disk write failed: {exc}", ""
    except AttributeError:
        # file_object lacks a .save() method — bad input
        return False, "Invalid file object received.", ""


def delete_upload(file_path: str) -> bool:
    """Delete a file from disk. Safe to call in finally blocks.

    Args:
        file_path: Absolute path to the file to delete.

    Returns:
        True if the file was deleted.
        False if the file did not exist or deletion failed.
    """
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            return True
        return False  # File does not exist — nothing to delete
    except OSError:
        return False


# ── Directory Management ─────────────────────────────────────


def ensure_directory(path: str) -> bool:
    """Create a directory (and parents) if it does not exist.

    Args:
        path: Absolute or relative path to the directory.

    Returns:
        True if the directory exists or was created.
        False if creation failed.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


# ── Report Persistence ────────────────────────────────────────


def save_report(report_id: str, report_data: dict) -> bool:
    """Serialize a verdict report to a JSON file.

    Saves to Config.REPORTS_FOLDER/{report_id}.json.
    Creates the reports directory if it does not already exist.

    Args:
        report_id: Unique identifier for the analysis run.
        report_data: Dictionary containing the full verdict report.

    Returns:
        True on successful write, False on any failure.
    """
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
        # TypeError / ValueError: report_data is not serializable
        return False


def load_report(report_id: str) -> tuple[bool, dict]:
    """Load a previously saved verdict report from disk.

    Reads from Config.REPORTS_FOLDER/{report_id}.json.

    Args:
        report_id: Unique identifier for the analysis run.

    Returns:
        (True,  report_dict) if the report was found and parsed.
        (False, {})          if not found, unreadable, or corrupt.
    """
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
