/**
 * Dashboard formatting helpers
 */

/** Map a verdict string to a { bg, text } color pair */
export function getVerdictColors(verdict) {
  const v = (verdict || "").toLowerCase();
  const map = {
    authentic:   { bg: "rgba(63,174,106,0.12)", text: "#3fae6a" },
    real:        { bg: "rgba(63,174,106,0.12)", text: "#3fae6a" },
    fake:        { bg: "rgba(217,90,90,0.12)", text: "#d95a5a" },
    forged:      { bg: "rgba(217,90,90,0.12)", text: "#d95a5a" },
    suspicious:  { bg: "rgba(217,164,65,0.12)",  text: "#d9a441" },
    uncertain:   { bg: "rgba(217,164,65,0.12)",  text: "#d9a441" },
  };
  return map[v] || { bg: "rgba(255,255,255,0.08)", text: "rgba(255,255,255,0.6)" };
}

/** Return an inline color for a 0-100 score */
export function getScoreColor(score) {
  const n = typeof score === "number" ? score : parseFloat(score);
  if (Number.isNaN(n)) return "rgba(255,255,255,0.5)";
  if (n >= 80) return "#3fae6a";
  if (n >= 50) return "#d9a441";
  return "#d95a5a";
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
