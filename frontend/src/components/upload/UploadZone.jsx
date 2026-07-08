import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileUp, Upload, X, CheckCircle } from 'lucide-react';
import { formatFileSize } from '../../utils/helpers';

const MAX_FILE_SIZE_MB = 20;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

/**
 * PDF drag-and-drop upload zone with validation and preview.
 *
 * @param {Object} props
 * @param {(file: File) => void} props.onFileSelect - Callback when a valid PDF is selected.
 * @param {boolean} [props.disabled]                - Disables all interaction.
 * @returns {JSX.Element}
 */
export default function UploadZone({ onFileSelect, disabled = false }) {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  /**
   * Validate a file against type and size constraints.
   * @param {File} f
   * @returns {string|null} Error message or null if valid.
   */
  function validate(f) {
    if (!f) return 'No file selected.';
    if (f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF files are accepted.';
    }
    if (f.size > MAX_FILE_SIZE_BYTES) {
      return `File exceeds ${MAX_FILE_SIZE_MB}MB limit (${formatFileSize(f.size)}).`;
    }
    return null;
  }

  const handleFile = useCallback(
    (f) => {
      setError('');
      const err = validate(f);
      if (err) {
        setError(err);
        setFile(null);
        return;
      }
      setFile(f);
    },
    []
  );

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    if (disabled) return;
    const dropped = e.dataTransfer.files?.[0];
    handleFile(dropped);
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setDragOver(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }

  function handleInputChange(e) {
    const selected = e.target.files?.[0];
    if (selected) handleFile(selected);
    e.target.value = '';
  }

  function handleBrowse() {
    if (!disabled) inputRef.current?.click();
  }

  function handleRemove() {
    setFile(null);
    setError('');
  }

  function handleAnalyze() {
    if (file && onFileSelect) onFileSelect(file);
  }

  const hasError = !!error;

  const borderColor = hasError
    ? 'rgba(239,68,68,0.6)'
    : dragOver
      ? '#f59e0b'
      : 'rgba(245,158,11,0.4)';

  const bgColor = dragOver
    ? 'rgba(245,158,11,0.08)'
    : 'rgba(255,255,255,0.03)';

  return (
    <motion.div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={!file ? handleBrowse : undefined}
      animate={{
        scale: dragOver ? 1.02 : 1,
        borderColor,
        backgroundColor: bgColor,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className="relative glass-card flex flex-col items-center justify-center text-center px-6 py-12 md:py-16 cursor-pointer select-none"
      style={{
        border: `2px dashed ${borderColor}`,
        borderRadius: 20,
        minHeight: 280,
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? 'none' : 'auto',
      }}
    >
      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleInputChange}
        disabled={disabled}
      />

      <AnimatePresence mode="wait">
        {/* ── File Selected State ── */}
        {file && !hasError ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center gap-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* File icon */}
            <div
              className="flex items-center justify-center rounded-2xl"
              style={{
                width: 64,
                height: 64,
                background: 'rgba(245,158,11,0.12)',
              }}
            >
              <CheckCircle size={32} color="#f59e0b" />
            </div>

            {/* File info */}
            <div>
              <p className="text-auth-silver font-medium text-base">
                {file.name}
              </p>
              <p className="text-auth-muted text-sm mt-1">
                {formatFileSize(file.size)}
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4 mt-2">
              <button
                onClick={handleAnalyze}
                className="btn-primary text-sm flex items-center gap-2 px-6 py-3"
              >
                <Upload size={16} />
                Analyze Document
              </button>
              <button
                onClick={handleRemove}
                className="flex items-center gap-1.5 text-sm transition-colors duration-200"
                style={{ color: 'rgba(229,229,229,0.5)' }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.color = '#d95a5a')
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.color = 'rgba(229,229,229,0.5)')
                }
              >
                <X size={14} />
                Remove
              </button>
            </div>
          </motion.div>
        ) : (
          /* ── Default / Drag-Over State ── */
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center gap-4"
          >
            <motion.div
              animate={{ y: dragOver ? -4 : 0 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="flex items-center justify-center rounded-2xl"
              style={{
                width: 72,
                height: 72,
                background: 'rgba(245,158,11,0.1)',
              }}
            >
              <FileUp size={36} color="#f59e0b" />
            </motion.div>

            <div>
              <h3 className="font-heading text-xl text-auth-silver">
                {dragOver ? 'Release to upload' : 'Drop your PDF here'}
              </h3>
              <p className="text-auth-muted text-sm mt-1.5">
                or click to browse
              </p>
            </div>

            <p className="text-xs" style={{ color: 'rgba(229,229,229,0.35)' }}>
              Max {MAX_FILE_SIZE_MB}MB • PDF only
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Error Message ── */}
      <AnimatePresence>
        {hasError && (
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.25 }}
            className="absolute bottom-4 text-sm font-medium"
            style={{ color: '#d95a5a' }}
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
