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
  const color = value > 70 ? '#f59e0b' : value >= 40 ? '#d9a441' : '#d95a5a';

  return (
    <div
      className="glass-card inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
      style={{ border: `1px solid ${color}33` }}
    >
      <Cpu size={16} color={color} />
      <span style={{ color: 'rgba(229,229,229,0.6)' }}>
        ML Confidence:
      </span>
      <span style={{ color }}>{formatConfidence(value)}</span>
    </div>
  );
}
