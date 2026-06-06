import { motion } from 'framer-motion';
import { FileText, X } from 'lucide-react';
import { formatFileSize, truncateFilename } from '../../utils/helpers';

/**
 * Displays selected PDF file details with a remove action.
 *
 * @param {Object} props
 * @param {File}       props.file     - The selected PDF File object.
 * @param {() => void} props.onRemove - Callback to clear the selection.
 * @returns {JSX.Element}
 */
export default function FilePreview({ file, onRemove }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="glass-card flex items-center gap-4 px-5 py-4"
      style={{ borderRadius: 12 }}
    >
      {/* PDF Icon */}
      <div
        className="flex-shrink-0 flex items-center justify-center rounded-xl"
        style={{
          width: 48,
          height: 48,
          background: 'rgba(14,165,233,0.1)',
        }}
      >
        <FileText size={24} color="#0ea5e9" />
      </div>

      {/* File Info */}
      <div className="flex-1 min-w-0">
        <p className="text-auth-silver text-sm font-medium truncate">
          {truncateFilename(file.name, 35)}
        </p>
        <p className="text-auth-muted text-xs mt-0.5">
          {formatFileSize(file.size)}
        </p>
        <p className="text-xs mt-1 font-medium" style={{ color: '#0ea5e9' }}>
          Ready for analysis
        </p>
      </div>

      {/* Remove Button */}
      <button
        onClick={onRemove}
        className="flex-shrink-0 flex items-center justify-center rounded-lg transition-colors duration-200"
        style={{
          width: 32,
          height: 32,
          color: 'rgba(226,232,240,0.4)',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
        onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(226,232,240,0.4)')}
        aria-label="Remove file"
      >
        <X size={18} />
      </button>
    </motion.div>
  );
}
