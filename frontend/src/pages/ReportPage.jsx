import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, FileText, ShieldCheck, AlertTriangle, Home, Loader2 } from "lucide-react";
import { getReportById } from "../services/api";
import ScoreRing from "../components/results/ScoreRing";

/* ═══════════════════════════════════════════
   Animation variant
   ═══════════════════════════════════════════ */

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

/* ═══════════════════════════════════════════
   Shared styles
   ═══════════════════════════════════════════ */

const glassCard = {
  background: "rgba(18,18,20,0.5)",
  backdropFilter: "blur(12px)",
  WebkitBackdropFilter: "blur(12px)",
  border: "1px solid rgba(245,158,11,0.15)",
  borderRadius: 16,
  padding: "20px 24px",
  marginBottom: 16,
};

const cardLabel = {
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "rgba(229,229,229,0.4)",
  margin: "0 0 12px",
};

/* ═══════════════════════════════════════════
   Result sub-components
   (mirrors AnalyzePage inline components)
   ═══════════════════════════════════════════ */

const ReasonsList = ({ reasons = [] }) => {
  if (!reasons.length) return null;
  return (
    <div style={glassCard}>
      <p style={cardLabel}>Key Findings</p>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {reasons.map((r, i) => (
          <li key={i} style={{ fontSize: 14, color: "rgba(229,229,229,0.7)", lineHeight: 1.7 }}>{r}</li>
        ))}
      </ul>
    </div>
  );
};

const BreakdownTable = ({ breakdown = {} }) => {
  const entries = Object.entries(breakdown);
  if (!entries.length) return null;
  return (
    <div style={glassCard}>
      <p style={cardLabel}>Score Breakdown</p>
      {entries.map(([key, val]) => (
        <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
          <span style={{ fontSize: 13, color: "rgba(229,229,229,0.6)", textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: "#e5e5e5", fontVariantNumeric: "tabular-nums" }}>{val}</span>
        </div>
      ))}
    </div>
  );
};

/* ═══════════════════════════════════════════
   Date formatter
   ═══════════════════════════════════════════ */

const fmtDate = (raw) => {
  if (!raw) return "";
  const d = new Date(raw);
  if (isNaN(d.getTime())) return String(raw);
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

/* ═══════════════════════════════════════════
   ReportPage
   ═══════════════════════════════════════════ */

const ReportPage = () => {
  const { reportId } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError("");

    getReportById(reportId)
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Report not found");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [reportId]);

  /* Safely extract fields */
  const r = report || {};
  const verdict = r.verdict ?? r.result?.verdict;
  const score = r.score ?? r.result?.score;
  const confidence = r.confidence ?? r.result?.confidence;
  const reasons = r.reasons || r.result?.reasons || [];
  const breakdown = r.breakdown || r.result?.breakdown || {};
  const filename = r.filename || r.file_name || "Document";
  const createdAt = r.created_at || r.timestamp;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "transparent",
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        color: "#e5e5e5",
        padding: "40px 24px 80px",
      }}
    >
      <div style={{ maxWidth: 900, margin: "0 auto" }}>

        {/* ═══ LOADING ═══ */}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: 120 }}>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
              style={{ color: "#f59e0b" }}
            >
              <Loader2 size={40} />
            </motion.div>
          </div>
        )}

        {/* ═══ ERROR / 404 ═══ */}
        {!loading && error && (
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            style={{ textAlign: "center", paddingTop: 80 }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                margin: "0 auto 24px",
                borderRadius: 18,
                background: "rgba(248,113,113,0.1)",
                border: "1px solid rgba(248,113,113,0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#f87171",
              }}
            >
              <AlertTriangle size={28} />
            </div>
            <h2
              style={{
                fontFamily: "'Helvetica Now Display','Helvetica Neue',Helvetica,Arial,sans-serif",
                fontWeight: 700,
                fontSize: 22,
                color: "#e5e5e5",
                margin: "0 0 8px",
              }}
            >
              Report Not Found
            </h2>
            <p style={{ fontSize: 14, color: "rgba(229,229,229,0.5)", margin: "0 0 32px", maxWidth: 380, marginLeft: "auto", marginRight: "auto" }}>
              {error}
            </p>
            <button
              onClick={() => navigate("/")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 14,
                fontWeight: 600,
                color: "#fff",
                background: "#f59e0b",
                border: "none",
                borderRadius: 12,
                padding: "12px 24px",
                cursor: "pointer",
                boxShadow: "0 0 20px rgba(245,158,11,0.25)",
              }}
            >
              <Home size={15} />
              Back to Home
            </button>
          </motion.div>
        )}

        {/* ═══ REPORT ═══ */}
        {!loading && !error && report && (
          <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.08 } } }}>

            {/* ── Top bar ── */}
            <motion.div
              variants={fadeUp}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 28,
              }}
            >
              <button
                onClick={() => navigate(-1)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  fontSize: 13,
                  fontWeight: 500,
                  color: "rgba(229,229,229,0.6)",
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: 10,
                  padding: "8px 16px",
                  cursor: "pointer",
                  transition: "background 0.2s, border-color 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.07)";
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
                }}
              >
                <ArrowLeft size={14} />
                Back
              </button>

              <span style={{ fontSize: 12, color: "rgba(229,229,229,0.25)", fontFamily: "monospace" }}>
                {reportId}
              </span>
            </motion.div>

            {/* ── Header card ── */}
            <motion.div
              variants={fadeUp}
              style={{
                ...glassCard,
                display: "flex",
                alignItems: "center",
                gap: 16,
                flexWrap: "wrap",
                padding: "24px 28px",
                marginBottom: 28,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: "rgba(245,158,11,0.1)",
                  border: "1px solid rgba(245,158,11,0.18)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#f59e0b",
                  flexShrink: 0,
                }}
              >
                <FileText size={20} />
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <h1
                  style={{
                    fontFamily: "'Helvetica Now Display','Helvetica Neue',Helvetica,Arial,sans-serif",
                    fontWeight: 700,
                    fontSize: 20,
                    color: "#e5e5e5",
                    margin: "0 0 4px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {filename}
                </h1>
                {createdAt && (
                  <p style={{ fontSize: 13, color: "rgba(229,229,229,0.4)", margin: 0 }}>
                    {fmtDate(createdAt)}
                  </p>
                )}
              </div>

              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#f59e0b",
                  background: "rgba(245,158,11,0.08)",
                  border: "1px solid rgba(245,158,11,0.2)",
                  borderRadius: 999,
                  padding: "6px 14px",
                  whiteSpace: "nowrap",
                }}
              >
                <ShieldCheck size={13} />
                Verified by AuthentIfy
              </span>
            </motion.div>

            {/* ── Focal ring ── */}
            <motion.div variants={fadeUp}>
              <ScoreRing
                score={score}
                verdict={verdict}
                confidence={confidence}
                timestamp={createdAt}
              />
            </motion.div>

            {/* ── Findings + breakdown ── */}
            <motion.div
              variants={fadeUp}
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                gap: 20,
              }}
            >
              <ReasonsList reasons={reasons} />
              <BreakdownTable breakdown={breakdown} />
            </motion.div>

          </motion.div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;
