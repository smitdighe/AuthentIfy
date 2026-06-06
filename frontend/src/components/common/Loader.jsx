import { motion } from 'framer-motion';

/**
 * Loading spinner with optional full-screen overlay.
 *
 * @param {Object} props
 * @param {string}  [props.text]    - Optional message displayed below the spinner.
 * @param {boolean} [props.overlay] - Full-screen overlay mode (default true).
 * @returns {JSX.Element}
 */
export default function Loader({ text, overlay = true }) {
  const spinner = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div
        className="w-12 h-12 rounded-full border-4 border-auth-border border-t-auth-accent animate-spin"
      />
      {text && (
        <p className="font-body text-sm text-auth-silver opacity-70">
          {text}
        </p>
      )}
    </div>
  );

  if (!overlay) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="flex items-center justify-center py-12"
      >
        {spinner}
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(176, 210, 210,0.9)' }}
    >
      {spinner}
    </motion.div>
  );
}
