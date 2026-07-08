import { motion } from 'framer-motion';
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.35, ease: 'easeOut' },
  }),
};

/**
 * Displays a list of detection findings from PDF analysis.
 *
 * @param {Object}   props
 * @param {string[]} props.reasons - Array of issue/reason strings.
 * @returns {JSX.Element}
 */
export default function ReasonsList({ reasons = [] }) {
  const hasReasons = reasons.length > 0;

  return (
    <div className="flex flex-col gap-4">
      {/* Section Heading */}
      <div className="flex items-center gap-2.5">
        <Shield size={20} color="#f59e0b" />
        <h3 className="font-heading text-lg text-auth-silver">
          Detection Findings
        </h3>
      </div>

      {/* Empty State */}
      {!hasReasons && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="glass-card flex items-center gap-3 px-5 py-4"
          style={{
            borderRadius: 12,
            border: '1px solid rgba(245,158,11,0.2)',
          }}
        >
          <CheckCircle size={22} color="#f59e0b" />
          <span className="text-sm font-medium" style={{ color: '#f59e0b' }}>
            No issues detected
          </span>
        </motion.div>
      )}

      {/* Reasons List */}
      {hasReasons && (
        <div className="flex flex-col gap-2.5">
          {reasons.map((reason, i) => (
            <motion.div
              key={i}
              custom={i}
              initial="hidden"
              animate="visible"
              variants={itemVariants}
              className="glass-card flex items-start gap-3 px-5 py-4"
              style={{
                borderRadius: 12,
                border: '1px solid rgba(239,68,68,0.15)',
              }}
            >
              <AlertTriangle
                size={18}
                color="#d9a441"
                className="flex-shrink-0 mt-0.5"
              />
              <span className="text-sm text-auth-silver leading-relaxed">
                {reason}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
