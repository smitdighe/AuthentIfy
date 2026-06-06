/**
 * Format an ISO date string into a human-readable format.
 * @param {string} isoString - ISO 8601 date string.
 * @returns {string} Formatted date e.g. "May 26, 2026 at 10:30 AM".
 */
export function formatDate(isoString) {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return 'Unknown date';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).replace(',', '').replace(/ at /, ' at ').replace(/(\d{4})/, '$1 at');
  } catch {
    return 'Unknown date';
  }
}

/**
 * Format a score as a clamped integer string (0–100).
 * @param {number} score - Raw score value.
 * @returns {string} Clamped integer string e.g. "82".
 */
export function formatScore(score) {
  const clamped = Math.min(100, Math.max(0, Math.round(Number(score) || 0)));
  return String(clamped);
}

/**
 * Get the theme color hex for a verdict label.
 * @param {string} verdict - One of "Genuine", "Suspicious", "Tampered".
 * @returns {string} Hex color string.
 */
export function getVerdictColor(verdict) {
  const colors = {
    Genuine: '#0ea5e9',
    Suspicious: '#f59e0b',
    Tampered: '#ef4444',
  };
  return colors[verdict] || '#0ea5e9';
}

/**
 * Get a translucent background color for a verdict label.
 * @param {string} verdict - One of "Genuine", "Suspicious", "Tampered".
 * @returns {string} RGBA background color string.
 */
export function getVerdictBg(verdict) {
  const backgrounds = {
    Genuine: 'rgba(14,165,233,0.15)',
    Suspicious: 'rgba(245,158,11,0.15)',
    Tampered: 'rgba(239,68,68,0.15)',
  };
  return backgrounds[verdict] || 'rgba(255,255,255,0.05)';
}

/**
 * Get the icon character for a verdict label.
 * @param {string} verdict - One of "Genuine", "Suspicious", "Tampered".
 * @returns {string} Unicode icon character.
 */
export function getVerdictIcon(verdict) {
  const icons = {
    Genuine: '✓',
    Suspicious: '⚠',
    Tampered: '✗',
  };
  return icons[verdict] || '?';
}

/**
 * Format a byte count into a human-readable file size.
 * @param {number} bytes - File size in bytes.
 * @returns {string} Formatted size e.g. "1.2 MB", "340 KB".
 */
export function formatFileSize(bytes) {
  if (bytes == null || isNaN(bytes) || bytes < 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = Number(bytes);

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return unitIndex === 0
    ? `${size} ${units[unitIndex]}`
    : `${size.toFixed(1).replace(/\.0$/, '')} ${units[unitIndex]}`;
}

/**
 * Truncate a filename to a maximum length, preserving the extension.
 * @param {string} filename  - Original filename.
 * @param {number} maxLength - Maximum total length (default 30).
 * @returns {string} Truncated filename e.g. "very-long-document-name...pdf".
 */
export function truncateFilename(filename, maxLength = 30) {
  if (!filename || filename.length <= maxLength) return filename || '';

  const dotIndex = filename.lastIndexOf('.');
  const ext = dotIndex !== -1 ? filename.slice(dotIndex + 1) : '';
  const name = dotIndex !== -1 ? filename.slice(0, dotIndex) : filename;

  const availableLength = maxLength - ext.length - 3; // 3 for "..."
  if (availableLength <= 0) return filename.slice(0, maxLength);

  return `${name.slice(0, availableLength)}...${ext}`;
}

/**
 * Format a confidence value as a percentage string.
 * @param {number} confidence - Confidence value (0–100 or 0–1).
 * @returns {string} Formatted percentage e.g. "91.2%".
 */
export function formatConfidence(confidence) {
  const value = Number(confidence) || 0;
  return `${value.toFixed(1)}%`;
}

/**
 * Validate an email address format.
 * @param {string} email - Email string to validate.
 * @returns {boolean} True if the email format is valid.
 */
export function isValidEmail(email) {
  if (!email || typeof email !== 'string') return false;
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email.trim());
}

/**
 * Validate a password meets minimum requirements.
 * @param {string} password - Password string to validate.
 * @returns {boolean} True if the password is at least 8 characters.
 */
export function isValidPassword(password) {
  if (!password || typeof password !== 'string') return false;
  return password.length >= 8;
}

/**
 * Get a descriptive label for an integrity score.
 * @param {number} score - Score value (0–100).
 * @returns {string} One of "Excellent", "Good", "Moderate", "Critical".
 */
export function getScoreLabel(score) {
  const value = Math.round(Number(score) || 0);
  if (value >= 80) return 'Excellent';
  if (value >= 60) return 'Good';
  if (value >= 40) return 'Moderate';
  return 'Critical';
}
