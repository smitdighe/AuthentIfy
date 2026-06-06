import { motion } from 'framer-motion';

/**
 * Format a deduction value with a minus sign and red color if non-zero.
 * @param {number} value
 * @returns {{ text: string, color: string }}
 */
function formatDeduction(value) {
  const num = Math.abs(Number(value) || 0);
  return {
    text: num > 0 ? `-${num}` : '0',
    color: num > 0 ? '#ef4444' : 'rgba(226,232,240,0.5)',
  };
}

const rows = [
  { key: 'starting_score', label: 'Starting Score', isDeduction: false },
  { key: 'metadata_deduction', label: 'Metadata Deductions', isDeduction: true },
  { key: 'ela_deduction', label: 'Vision Deductions', isDeduction: true },
  { key: 'ocr_deduction', label: 'OCR Deductions', isDeduction: true },
  { key: 'template_deduction', label: 'Template Deductions', isDeduction: true },
  { key: 'ml_deduction', label: 'ML Anomaly', isDeduction: true },
];

/**
 * Score deduction breakdown table.
 *
 * @param {Object} props
 * @param {Object} props.breakdown - Score breakdown object from the API.
 * @returns {JSX.Element}
 */
export default function BreakdownTable({ breakdown = {} }) {
  const finalScore = Math.round(Number(breakdown.final_score) || 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="glass-card overflow-hidden"
      style={{ borderRadius: 16 }}
    >
      {/* Heading */}
      <div
        className="px-6 py-4"
        style={{ borderBottom: '1px solid rgba(226,232,240,0.08)' }}
      >
        <h3 className="font-heading text-lg text-auth-silver">
          Score Breakdown
        </h3>
      </div>

      {/* Rows */}
      <div className="px-6 py-2">
        {rows.map((row) => {
          const raw = breakdown[row.key];
          const { text, color } = row.isDeduction
            ? formatDeduction(raw)
            : { text: String(Math.round(Number(raw) || 0)), color: '#0ea5e9' };

          return (
            <div
              key={row.key}
              className="flex items-center justify-between py-3"
              style={{ borderBottom: '1px solid rgba(226,232,240,0.05)' }}
            >
              <span
                className="text-sm"
                style={{ color: 'rgba(226,232,240,0.7)' }}
              >
                {row.label}
              </span>
              <span
                className="text-sm font-semibold tabular-nums"
                style={{ color }}
              >
                {text}
              </span>
            </div>
          );
        })}

        {/* Final Score */}
        <div
          className="flex items-center justify-between py-4 mt-1"
          style={{ borderTop: '1px solid rgba(14,165,233,0.25)' }}
        >
          <span className="text-sm font-bold text-auth-silver">
            Final Score
          </span>
          <span
            className="text-lg font-bold font-heading"
            style={{ color: '#0ea5e9' }}
          >
            {finalScore}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
