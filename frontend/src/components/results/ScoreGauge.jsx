import { useState, useEffect } from 'react';

const SIZE = 200;
const STROKE_WIDTH = 12;
const RADIUS = (SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * Get arc color based on score range.
 * @param {number} score
 * @returns {string} Hex color.
 */
function getArcColor(score) {
  if (score >= 80) return '#0ea5e9';
  if (score >= 50) return '#f59e0b';
  return '#ef4444';
}

/**
 * Circular SVG score gauge with animated arc fill.
 *
 * @param {Object} props
 * @param {number} props.score   - Integrity score (0–100).
 * @param {string} props.verdict - Verdict label (unused visually, available for extension).
 * @returns {JSX.Element}
 */
export default function ScoreGauge({ score, verdict }) {
  const [offset, setOffset] = useState(CIRCUMFERENCE);
  const clampedScore = Math.min(100, Math.max(0, Math.round(score || 0)));
  const color = getArcColor(clampedScore);
  const targetOffset = CIRCUMFERENCE - (clampedScore / 100) * CIRCUMFERENCE;

  // Animate arc on mount
  useEffect(() => {
    const timeout = setTimeout(() => {
      setOffset(targetOffset);
    }, 80);
    return () => clearTimeout(timeout);
  }, [targetOffset]);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: SIZE, height: SIZE }}>
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="transform -rotate-90"
      >
        {/* Background arc */}
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="rgba(226,232,240,0.1)"
          strokeWidth={STROKE_WIDTH}
        />

        {/* Foreground arc */}
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE_WIDTH}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
            filter: `drop-shadow(0 0 8px ${color}66)`,
          }}
        />
      </svg>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-heading leading-none"
          style={{ fontSize: 48, color }}
        >
          {clampedScore}
        </span>
        <span
          className="font-heading mt-1"
          style={{ fontSize: 14, color: 'rgba(226,232,240,0.4)' }}
        >
          / 100
        </span>
      </div>
    </div>
  );
}
