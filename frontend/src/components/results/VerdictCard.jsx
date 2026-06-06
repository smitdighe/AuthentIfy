import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  getVerdictColor,
  getVerdictBg,
  getVerdictIcon,
  formatDate,
  formatConfidence,
} from '../../utils/helpers';

/**
 * Prominent verdict display card with animated score counter and verdict glow.
 *
 * @param {Object} props
 * @param {'Genuine'|'Suspicious'|'Tampered'} props.verdict    - Analysis verdict.
 * @param {number}                            props.score      - Integrity score (0–100).
 * @param {number}                            props.confidence - Confidence percentage.
 * @param {string}                            props.timestamp  - ISO date string.
 * @returns {JSX.Element}
 */
export default function VerdictCard({ verdict, score, confidence, timestamp }) {
  const [displayScore, setDisplayScore] = useState(0);
  const color = getVerdictColor(verdict);
  const bg = getVerdictBg(verdict);
  const icon = getVerdictIcon(verdict);
  const targetScore = Math.min(100, Math.max(0, Math.round(score || 0)));

  // Animate score counting up
  useEffect(() => {
    if (targetScore === 0) {
      setDisplayScore(0);
      return;
    }

    let current = 0;
    const step = Math.max(1, Math.floor(targetScore / 40));
    const interval = setInterval(() => {
      current += step;
      if (current >= targetScore) {
        current = targetScore;
        clearInterval(interval);
      }
      setDisplayScore(current);
    }, 30);

    return () => clearInterval(interval);
  }, [targetScore]);

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative glass-card overflow-hidden"
      style={{
        border: `1px solid ${color}33`,
        borderRadius: 20,
        padding: '40px 32px',
      }}
    >
      {/* Glow background */}
      <div
        className="absolute inset-0 animate-pulse-slow pointer-events-none"
        style={{
          background: `radial-gradient(ellipse at center, ${color}12 0%, transparent 70%)`,
        }}
      />

      <div className="relative z-10 flex flex-col items-center gap-6">
        {/* ── Verdict Badge ── */}
        <motion.div
          initial={{ y: -12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full font-bold text-sm uppercase tracking-wider"
          style={{
            background: bg,
            color,
            border: `1px solid ${color}44`,
          }}
        >
          <span className="text-base">{icon}</span>
          {verdict}
        </motion.div>

        {/* ── Score Display ── */}
        <div className="flex items-baseline gap-1">
          <span
            className="font-heading leading-none"
            style={{
              fontSize: 80,
              color,
            }}
          >
            {displayScore}
          </span>
          <span
            className="font-heading"
            style={{
              fontSize: 28,
              color: `${color}88`,
            }}
          >
            /100
          </span>
        </div>

        {/* ── Bottom Row ── */}
        <motion.div
          initial={{ y: 12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.35, duration: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-8 w-full"
        >
          <span
            className="text-sm font-medium"
            style={{ color: 'rgba(226,232,240,0.6)' }}
          >
            <span style={{ color }}>
              {formatConfidence(confidence)}
            </span>{' '}
            confidence
          </span>

          <span
            className="hidden sm:block w-1 h-1 rounded-full"
            style={{ background: 'rgba(226,232,240,0.2)' }}
          />

          <span
            className="text-sm"
            style={{ color: 'rgba(226,232,240,0.4)' }}
          >
            Analyzed {formatDate(timestamp)}
          </span>
        </motion.div>
      </div>
    </motion.div>
  );
}
