import { FileSearch, ChevronLeft, ChevronRight } from "lucide-react";
import ReportRow from "./ReportRow";

/* ── Skeleton row (pulse animation) ── */
const skeletonKeyframes = `
@keyframes skeletonPulse {
  0%, 100% { opacity: 0.08; }
  50%      { opacity: 0.16; }
}
`;

const SkeletonBar = ({ width }) => (
  <div
    style={{
      width,
      height: 14,
      borderRadius: 6,
      background: "rgba(255,255,255,0.12)",
      animation: "skeletonPulse 1.6s ease-in-out infinite",
    }}
  />
);

const SkeletonRow = ({ delay }) => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "1fr auto auto auto auto",
      alignItems: "center",
      gap: 16,
      padding: "14px 20px",
      animationDelay: `${delay}ms`,
    }}
  >
    <SkeletonBar width="60%" />
    <SkeletonBar width={72} />
    <SkeletonBar width={36} />
    <SkeletonBar width={90} />
    <div style={{ display: "flex", gap: 6 }}>
      <SkeletonBar width={64} />
      <SkeletonBar width={32} />
    </div>
  </div>
);

/* ── Pagination button ── */
const PagBtn = ({ children, disabled, onClick, style: extra }) => (
  <button
    disabled={disabled}
    onClick={onClick}
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      fontSize: 13,
      fontWeight: 500,
      color: disabled ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.65)",
      background: disabled ? "transparent" : "rgba(255,255,255,0.04)",
      border: "1px solid",
      borderColor: disabled ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.1)",
      borderRadius: 8,
      padding: "6px 14px",
      cursor: disabled ? "not-allowed" : "pointer",
      transition: "all 0.2s ease",
      ...extra,
    }}
    onMouseEnter={(e) => {
      if (!disabled) {
        e.currentTarget.style.background = "rgba(255,255,255,0.08)";
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.18)";
      }
    }}
    onMouseLeave={(e) => {
      if (!disabled) {
        e.currentTarget.style.background = "rgba(255,255,255,0.04)";
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
      }
    }}
  >
    {children}
  </button>
);

/* ── Main component ── */
const HistoryTable = ({
  reports = [],
  total,
  page = 1,
  pages = 1,
  onPageChange,
  onDelete,
  loading = false,
}) => {
  /* ── Loading state ── */
  if (loading) {
    return (
      <div style={wrapperStyle}>
        <style>{skeletonKeyframes}</style>
        <HeaderRow />
        <Divider />
        {[0, 1, 2].map((i) => (
          <SkeletonRow key={i} delay={i * 120} />
        ))}
      </div>
    );
  }

  /* ── Empty state ── */
  if (!reports || reports.length === 0) {
    return (
      <div style={wrapperStyle}>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "56px 24px",
            gap: 12,
          }}
        >
          <FileSearch
            size={40}
            strokeWidth={1.4}
            style={{ color: "rgba(255,255,255,0.18)", marginBottom: 4 }}
          />
          <span
            style={{
              fontSize: 16,
              fontWeight: 600,
              color: "rgba(255,255,255,0.45)",
            }}
          >
            No reports yet
          </span>
          <a
            href="/analyze"
            style={{
              fontSize: 14,
              fontWeight: 500,
              color: "#34d399",
              textDecoration: "none",
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#6ee7b7")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#34d399")}
          >
            Analyze your first document →
          </a>
        </div>
      </div>
    );
  }

  /* ── Normal state ── */
  return (
    <div style={wrapperStyle}>
      <HeaderRow />
      <Divider />

      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {reports.map((r) => (
          <ReportRow
            key={r.report_uuid}
            report={r}
            onDelete={onDelete}
            onView={() => {
              window.location.href = `/report/${r.report_uuid}`;
            }}
          />
        ))}
      </div>

      {/* Pagination footer */}
      {pages > 1 && (
        <>
          <Divider />
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 20px",
            }}
          >
            <PagBtn
              disabled={page <= 1}
              onClick={() => onPageChange?.(page - 1)}
            >
              <ChevronLeft size={14} />
              Previous
            </PagBtn>

            <span
              style={{
                fontSize: 13,
                color: "rgba(255,255,255,0.4)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              Page{" "}
              <span style={{ color: "#34d399", fontWeight: 600 }}>{page}</span>{" "}
              of {pages}
            </span>

            <PagBtn
              disabled={page >= pages}
              onClick={() => onPageChange?.(page + 1)}
            >
              Next
              <ChevronRight size={14} />
            </PagBtn>
          </div>
        </>
      )}
    </div>
  );
};

/* ── Shared pieces ── */

const wrapperStyle = {
  background: "rgba(255, 255, 255, 0.03)",
  backdropFilter: "blur(24px)",
  WebkitBackdropFilter: "blur(24px)",
  border: "1px solid rgba(255, 255, 255, 0.06)",
  borderRadius: 16,
  overflow: "hidden",
};

const headerCells = ["Filename", "Verdict", "Score", "Date", "Actions"];

const HeaderRow = () => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "1fr auto auto auto auto",
      alignItems: "center",
      gap: 16,
      padding: "12px 20px",
    }}
  >
    {headerCells.map((label) => (
      <span
        key={label}
        style={{
          fontSize: 11,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "rgba(255,255,255,0.3)",
        }}
      >
        {label}
      </span>
    ))}
  </div>
);

const Divider = () => (
  <div
    style={{
      height: 1,
      background: "rgba(255,255,255,0.06)",
    }}
  />
);

export default HistoryTable;
