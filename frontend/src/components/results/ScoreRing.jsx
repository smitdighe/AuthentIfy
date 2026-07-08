import { useState, useEffect, useRef } from "react";

/**
 * Merged authenticity display: a verdict-colored circular progress ring
 * whose fill and center number animate from 0 to the score on mount.
 * Verdict pill sits above, confidence + timestamp below, all on a subtle
 * verdict-tinted glass surface.
 *
 * @param {Object} props
 * @param {number}  props.score      - Integrity score (0–100).
 * @param {string}  props.verdict    - "Genuine" | "Suspicious" | "Tampered".
 * @param {number}  [props.confidence] - Confidence percentage.
 * @param {string}  [props.timestamp]  - Optional ISO date string.
 * @param {number}  [props.size]       - Ring diameter in px (default 200).
 */

const VERDICT = {
  genuine: { color: "#3fae6a", label: "Genuine", icon: "✓" },
  authentic: { color: "#3fae6a", label: "Genuine", icon: "✓" },
  suspicious: { color: "#d9a441", label: "Suspicious", icon: "⚠" },
  tampered: { color: "#d95a5a", label: "Tampered", icon: "✗" },
  forged: { color: "#d95a5a", label: "Tampered", icon: "✗" },
};

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}

export default function ScoreRing({
  score,
  verdict,
  confidence,
  timestamp,
  size = 200,
}) {
  const STROKE = 14;
  const radius = (size - STROKE) / 2;
  const circumference = 2 * Math.PI * radius;

  const target = Math.min(100, Math.max(0, Math.round(Number(score) || 0)));
  const v = VERDICT[(verdict || "").toLowerCase()] || VERDICT.suspicious;
  const [r, g, b] = hexToRgb(v.color);
  const rgba = (a) => `rgba(${r},${g},${b},${a})`;

  const [display, setDisplay] = useState(0);
  const [offset, setOffset] = useState(circumference);
  const rafRef = useRef(null);

  useEffect(() => {
    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    const filled = circumference - (target / 100) * circumference;

    if (reduce) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDisplay(target);
      setOffset(filled);
      return;
    }

    // arc fill via CSS transition (offset state), number via rAF
    const t = setTimeout(() => setOffset(filled), 60);
    const DURATION = 1100;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / DURATION);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(eased * target));
      if (p < 1) rafRef.current = requestAnimationFrame(tick);
      else setDisplay(target);
    };
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      clearTimeout(t);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, circumference]);

  const fmtDate = (raw) => {
    if (!raw) return "";
    const d = new Date(raw);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div
      style={{
        background: rgba(0.06),
        border: `1px solid ${rgba(0.22)}`,
        borderRadius: 20,
        padding: "32px 28px 28px",
        marginBottom: 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 20,
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
    >
      {/* Verdict pill */}
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 7,
          padding: "7px 16px",
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: v.color,
          background: rgba(0.12),
          border: `1px solid ${rgba(0.35)}`,
        }}
      >
        <span style={{ fontSize: 14 }}>{v.icon}</span>
        {v.label}
      </span>

      {/* Ring */}
      <div style={{ position: "relative", width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ transform: "rotate(-90deg)" }}
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(245,158,11,0.10)"
            strokeWidth={STROKE}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={v.color}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition:
                "stroke-dashoffset 1.1s cubic-bezier(0.25,0.46,0.45,0.94)",
              filter: `drop-shadow(0 0 10px ${rgba(0.4)})`,
            }}
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontSize: size * 0.26,
              fontWeight: 700,
              lineHeight: 1,
              letterSpacing: "-0.03em",
              color: v.color,
              fontVariantNumeric: "tabular-nums",
              fontFamily:
                "'Helvetica Now Display','Helvetica Neue',Helvetica,Arial,sans-serif",
            }}
          >
            {display}
          </span>
          <span
            style={{
              fontSize: 13,
              marginTop: 4,
              fontWeight: 600,
              color: "rgba(229,229,229,0.4)",
            }}
          >
            / 100
          </span>
        </div>
      </div>

      {/* Meta row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: 12,
          fontSize: 13,
          color: "rgba(229,229,229,0.55)",
        }}
      >
        {confidence != null && (
          <span>
            <span style={{ color: v.color, fontWeight: 600 }}>
              {Number(confidence).toFixed(1)}%
            </span>{" "}
            confidence
          </span>
        )}
        {confidence != null && timestamp && (
          <span
            style={{
              width: 3,
              height: 3,
              borderRadius: 999,
              background: "rgba(229,229,229,0.25)",
            }}
          />
        )}
        {timestamp && (
          <span style={{ color: "rgba(229,229,229,0.4)" }}>
            Analyzed {fmtDate(timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}
