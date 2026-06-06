/**
 * Dashboard formatting helpers
 */

/** Map a verdict string to a { bg, text } color pair */
export function getVerdictColors(verdict) {
  const v = (verdict || "").toLowerCase();
  const map = {
    authentic:   { bg: "rgba(52,211,153,0.12)", text: "#34d399" },
    real:        { bg: "rgba(52,211,153,0.12)", text: "#34d399" },
    fake:        { bg: "rgba(248,113,113,0.12)", text: "#f87171" },
    forged:      { bg: "rgba(248,113,113,0.12)", text: "#f87171" },
    suspicious:  { bg: "rgba(251,191,36,0.12)",  text: "#fbbf24" },
    uncertain:   { bg: "rgba(251,191,36,0.12)",  text: "#fbbf24" },
  };
  return map[v] || { bg: "rgba(255,255,255,0.08)", text: "rgba(255,255,255,0.6)" };
}

/** Return an inline color for a 0-100 score */
export function getScoreColor(score) {
  const n = typeof score === "number" ? score : parseFloat(score);
  if (Number.isNaN(n)) return "rgba(255,255,255,0.5)";
  if (n >= 80) return "#34d399";
  if (n >= 50) return "#fbbf24";
  return "#f87171";
}

/** Format an ISO / epoch date into a short readable string */
export function formatDate(raw) {
  if (!raw) return "—";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return String(raw);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
