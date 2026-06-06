import { Cpu } from 'lucide-react';
import { formatConfidence } from '../../utils/helpers';

/**
 * Pill badge displaying ML confidence with color-coded styling.
 *
 * @param {Object} props
 * @param {number} props.confidence - Confidence value (0–100).
 * @returns {JSX.Element}
 */
export default function ConfidenceBadge({ confidence }) {
  const value = Number(confidence) || 0;
  const color = value > 70 ? '#0ea5e9' : value >= 40 ? '#f59e0b' : '#ef4444';

  return (
    <div
      className="glass-card inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
      style={{ border: `1px solid ${color}33` }}
    >
      <Cpu size={16} color={color} />
      <span style={{ color: 'rgba(226,232,240,0.6)' }}>
        ML Confidence:
      </span>
      <span style={{ color }}>{formatConfidence(value)}</span>
    </div>
  );
}
