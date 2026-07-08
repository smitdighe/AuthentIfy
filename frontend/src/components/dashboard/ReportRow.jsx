import { useState } from "react";
import { Trash2, Eye } from "lucide-react";
import { getVerdictColors, getScoreColor, formatDate } from "./helpers";

const grid = {
  display: "grid",
  gridTemplateColumns: "1fr auto auto auto auto",
  alignItems: "center",
  gap: 16,
  padding: "14px 20px",
  borderRadius: 10,
  transition: "background 0.2s ease",
  cursor: "default",
};

const ReportRow = ({ report, onDelete, onView }) => {
  const [hovered, setHovered] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const {
    report_uuid,
    filename,
    verdict,
    score,
    created_at,
  } = report;

  const verdictColors = getVerdictColors(verdict);
  const scoreColor = getScoreColor(score);

  const handleDelete = () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    onDelete?.(report_uuid);
    setConfirming(false);
  };

  const handleDeleteBlur = () => setConfirming(false);

  return (
    <div
      style={{
        ...grid,
        background: hovered
          ? "rgba(255, 255, 255, 0.04)"
          : "transparent",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => {
        setHovered(false);
        setConfirming(false);
      }}
    >
      {/* Filename */}
      <span
        style={{
          fontSize: 14,
          fontWeight: 500,
          color: "#e5e5e5",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
        title={filename}
      >
        {filename}
      </span>

      {/* Verdict badge */}
      <span
        style={{
          fontSize: 12,
          fontWeight: 600,
          textTransform: "capitalize",
          color: verdictColors.text,
          background: verdictColors.bg,
          borderRadius: 999,
          padding: "4px 12px",
          whiteSpace: "nowrap",
        }}
      >
        {verdict}
      </span>

      {/* Score */}
      <span
        style={{
          fontSize: 14,
          fontWeight: 700,
          color: scoreColor,
          fontVariantNumeric: "tabular-nums",
          minWidth: 36,
          textAlign: "right",
        }}
      >
        {score != null ? score : "—"}
      </span>

      {/* Date */}
      <span
        style={{
          fontSize: 13,
          color: "rgba(255, 255, 255, 0.4)",
          whiteSpace: "nowrap",
          minWidth: 90,
          textAlign: "right",
        }}
      >
        {formatDate(created_at)}
      </span>

      {/* Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        {/* View button */}
        <button
          onClick={() => onView?.(report_uuid)}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 5,
            fontSize: 13,
            fontWeight: 500,
            color: "#fbbf24",
            background: "rgba(167, 139, 250, 0.1)",
            border: "1px solid rgba(167, 139, 250, 0.2)",
            borderRadius: 8,
            padding: "5px 12px",
            cursor: "pointer",
            transition: "background 0.2s ease, border-color 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(167,139,250,0.18)";
            e.currentTarget.style.borderColor = "rgba(167,139,250,0.4)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(167,139,250,0.1)";
            e.currentTarget.style.borderColor = "rgba(167,139,250,0.2)";
          }}
        >
          <Eye size={14} />
          View
        </button>

        {/* Delete icon button */}
        <button
          onClick={handleDelete}
          onBlur={handleDeleteBlur}
          title={confirming ? "Click again to confirm" : "Delete report"}
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 32,
            height: 32,
            border: "1px solid",
            borderColor: confirming
              ? "rgba(217,90,90,0.5)"
              : "rgba(255,255,255,0.08)",
            borderRadius: 8,
            background: confirming
              ? "rgba(217,90,90,0.15)"
              : "transparent",
            color: confirming ? "#d95a5a" : "rgba(255,255,255,0.35)",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            if (!confirming) {
              e.currentTarget.style.color = "#d95a5a";
              e.currentTarget.style.borderColor = "rgba(217,90,90,0.3)";
              e.currentTarget.style.background = "rgba(217,90,90,0.08)";
            }
          }}
          onMouseLeave={(e) => {
            if (!confirming) {
              e.currentTarget.style.color = "rgba(255,255,255,0.35)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
              e.currentTarget.style.background = "transparent";
            }
          }}
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
};

export default ReportRow;
