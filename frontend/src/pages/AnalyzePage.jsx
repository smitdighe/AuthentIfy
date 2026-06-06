import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, RotateCcw, LayoutDashboard, AlertTriangle, CheckCircle2, FileText, Loader2 } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { analyzeDocument } from "../api";

/* ═══════════════════════════════════════════
   Animation variants
   ═══════════════════════════════════════════ */

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25 } },
};

/* ═══════════════════════════════════════════
   Pipeline steps shown during loading
   ═══════════════════════════════════════════ */

const PIPELINE = [
  "Extracting metadata...",
  "Running ELA analysis...",
  "Performing OCR...",
  "Checking templates...",
  "Running ML detection...",
];

/* ═══════════════════════════════════════════
   Inline sub-components
   (will be extracted into separate files later)
   ═══════════════════════════════════════════ */

/* ── UploadZone ── */
const UploadZone = ({ onFileSelect }) => {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer?.files?.[0];
    if (f && f.type === "application/pdf") onFileSelect(f);
  };

  const handleChange = (e) => {
    const f = e.target.files?.[0];
    if (f) onFileSelect(f);
  };

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${dragging ? "#0ea5e9" : "rgba(255,255,255,0.12)"}`,
        borderRadius: 16,
        padding: "56px 32px",
        textAlign: "center",
        cursor: "pointer",
        background: dragging ? "rgba(14,165,233,0.06)" : "rgba(255,255,255,0.02)",
        transition: "all 0.25s ease",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleChange}
        style={{ display: "none" }}
      />
      <div
        style={{
          width: 56,
          height: 56,
          margin: "0 auto 20px",
          borderRadius: 16,
          background: "rgba(14,165,233,0.1)",
          border: "1px solid rgba(14,165,233,0.18)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#34d399",
        }}
      >
        <Upload size={24} />
      </div>
      <p style={{ fontSize: 16, fontWeight: 600, color: "#0ea5e9", margin: "0 0 8px" }}>
        Drop your PDF here or click to browse
      </p>
      <p style={{ fontSize: 13, color: "rgba(226,232,240,0.45)", margin: 0 }}>
        Supports PDF files up to 20 MB
      </p>
    </motion.div>
  );
};

/* ── File preview strip ── */
const FileStrip = ({ file, onRemove, onAnalyze, disabled }) => (
  <motion.div
    variants={fadeUp}
    initial="hidden"
    animate="visible"
    style={{
      display: "flex",
      alignItems: "center",
      gap: 14,
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 14,
      padding: "14px 20px",
      marginTop: 16,
    }}
  >
    <FileText size={20} style={{ color: "#34d399", flexShrink: 0 }} />
    <div style={{ flex: 1, minWidth: 0 }}>
      <p style={{ fontSize: 14, fontWeight: 500, color: "#0ea5e9", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {file.name}
      </p>
      <p style={{ fontSize: 12, color: "rgba(226,232,240,0.4)", margin: "2px 0 0" }}>
        {(file.size / 1024).toFixed(1)} KB
      </p>
    </div>
    <button onClick={onRemove} style={linkBtn} title="Remove">✕</button>
    <button onClick={onAnalyze} disabled={disabled} style={primaryBtn}>
      Analyze
    </button>
  </motion.div>
);

/* ── VerdictCard ── */
const VerdictCard = ({ verdict }) => {
  const v = (verdict || "").toLowerCase();
  const map = {
    genuine: { color: "#34d399", bg: "rgba(52,211,153,0.08)", border: "rgba(52,211,153,0.2)" },
    authentic: { color: "#34d399", bg: "rgba(52,211,153,0.08)", border: "rgba(52,211,153,0.2)" },
    suspicious: { color: "#fbbf24", bg: "rgba(251,191,36,0.08)", border: "rgba(251,191,36,0.2)" },
    tampered: { color: "#f87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.2)" },
    forged: { color: "#f87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.2)" },
  };
  const s = map[v] || map.suspicious;

  return (
    <div style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 16, padding: "28px 24px", marginBottom: 20 }}>
      <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "rgba(226,232,240,0.45)", margin: "0 0 8px" }}>Verdict</p>
      <p style={{ fontSize: 28, fontWeight: 700, color: s.color, margin: 0, textTransform: "capitalize", fontFamily: "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif" }}>
        {verdict}
      </p>
    </div>
  );
};

/* ── ReasonsList ── */
const ReasonsList = ({ reasons = [] }) => {
  if (!reasons.length) return null;
  return (
    <div style={glassCard}>
      <p style={cardLabel}>Key Findings</p>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {reasons.map((r, i) => (
          <li key={i} style={{ fontSize: 14, color: "rgba(226,232,240,0.7)", lineHeight: 1.7 }}>{r}</li>
        ))}
      </ul>
    </div>
  );
};

/* ── ScoreGauge ── */
const ScoreGauge = ({ score }) => {
  const n = typeof score === "number" ? score : parseFloat(score) || 0;
  const color = n >= 80 ? "#34d399" : n >= 50 ? "#fbbf24" : "#f87171";
  return (
    <div style={{ ...glassCard, textAlign: "center", marginBottom: 16 }}>
      <p style={cardLabel}>Authenticity Score</p>
      <p style={{ fontSize: 48, fontWeight: 700, color, margin: "8px 0 0", fontFamily: "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif", lineHeight: 1 }}>
        {Math.round(n)}
      </p>
      <p style={{ fontSize: 12, color: "rgba(226,232,240,0.4)", margin: "6px 0 0" }}>out of 100</p>
    </div>
  );
};

/* ── ConfidenceBadge ── */
const ConfidenceBadge = ({ confidence }) => (
  <div style={{ ...glassCard, textAlign: "center", marginBottom: 16, padding: "16px 20px" }}>
    <p style={{ ...cardLabel, marginBottom: 4 }}>Confidence</p>
    <p style={{ fontSize: 20, fontWeight: 700, color: "#a78bfa", margin: 0 }}>
      {confidence != null ? `${confidence}%` : "—"}
    </p>
  </div>
);

/* ── BreakdownTable ── */
const BreakdownTable = ({ breakdown = {} }) => {
  const entries = Object.entries(breakdown);
  if (!entries.length) return null;
  return (
    <div style={glassCard}>
      <p style={cardLabel}>Score Breakdown</p>
      {entries.map(([key, val]) => (
        <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
          <span style={{ fontSize: 13, color: "rgba(226,232,240,0.6)", textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: "#0ea5e9", fontVariantNumeric: "tabular-nums" }}>{val}</span>
        </div>
      ))}
    </div>
  );
};

/* ═══════════════════════════════════════════
   AnalyzePage
   ═══════════════════════════════════════════ */

const AnalyzePage = () => {
  const { user, token } = useAuth();

  // "idle" | "loading" | "results" | "error"
  const [stage, setStage] = useState("idle");
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [visibleSteps, setVisibleSteps] = useState([]);

  /* Pipeline step animation during loading */
  const stepTimers = useRef([]);

  const startPipeline = () => {
    setVisibleSteps([]);
    stepTimers.current.forEach(clearTimeout);
    stepTimers.current = PIPELINE.map((_, i) =>
      setTimeout(() => setVisibleSteps((prev) => [...prev, i]), (i + 1) * 1500)
    );
  };

  const stopPipeline = () => {
    stepTimers.current.forEach(clearTimeout);
    stepTimers.current = [];
  };

  useEffect(() => () => stopPipeline(), []);

  /* Handlers */
  const handleFileSelect = (f) => setFile(f);

  const handleAnalyze = async () => {
    if (!file) return;
    setStage("loading");
    setErrorMsg("");
    startPipeline();

    try {
      const data = await analyzeDocument(file, token);
      setResults(data);
      setStage("results");
    } catch (err) {
      setErrorMsg(err.message || "Analysis failed");
      setStage("error");
    } finally {
      stopPipeline();
    }
  };

  const handleReset = () => {
    setFile(null);
    setResults(null);
    setErrorMsg("");
    setVisibleSteps([]);
    setStage("idle");
  };

  /* Result data (safely destructure) */
  const r = results || {};
  const verdict = r.verdict || r.result?.verdict;
  const score = r.score ?? r.result?.score;
  const confidence = r.confidence ?? r.result?.confidence;
  const reasons = r.reasons || r.result?.reasons || [];
  const breakdown = r.breakdown || r.result?.breakdown || {};
  const reportId = r.report_uuid || r.report_id;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#192837",
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        color: "#0ea5e9",
        padding: "40px 24px 80px",
      }}
    >
      <div style={{ maxWidth: 900, margin: "0 auto" }}>

        {/* ── Header ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} style={{ marginBottom: 36 }}>
          <h1 style={{ fontFamily: "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif", fontWeight: 700, fontSize: "clamp(1.5rem, 3vw, 2rem)", color: "#0ea5e9", margin: "0 0 8px" }}>
            Document Analysis
          </h1>
          <p style={{ fontSize: 15, color: "rgba(226,232,240,0.5)", margin: 0 }}>
            Upload a PDF to begin forensic verification
          </p>
        </motion.div>

        <AnimatePresence mode="wait">

          {/* ═══ IDLE STATE ═══ */}
          {stage === "idle" && (
            <motion.div key="idle" variants={fadeUp} initial="hidden" animate="visible" exit="exit">
              <UploadZone onFileSelect={handleFileSelect} />
              {file && (
                <FileStrip
                  file={file}
                  onRemove={() => setFile(null)}
                  onAnalyze={handleAnalyze}
                  disabled={false}
                />
              )}
            </motion.div>
          )}

          {/* ═══ LOADING STATE ═══ */}
          {stage === "loading" && (
            <motion.div key="loading" variants={fadeUp} initial="hidden" animate="visible" exit="exit" style={{ textAlign: "center", paddingTop: 48 }}>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
                style={{ display: "inline-flex", marginBottom: 24, color: "#34d399" }}
              >
                <Loader2 size={40} />
              </motion.div>

              <p style={{ fontSize: 18, fontWeight: 600, color: "#0ea5e9", margin: "0 0 8px" }}>
                Analyzing document…
              </p>
              <p style={{ fontSize: 14, color: "rgba(226,232,240,0.45)", margin: "0 0 32px" }}>
                {file?.name}
              </p>

              {/* Pipeline steps */}
              <div style={{ maxWidth: 320, margin: "0 auto", textAlign: "left" }}>
                {PIPELINE.map((step, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -12 }}
                    animate={visibleSteps.includes(i) ? { opacity: 1, x: 0 } : { opacity: 0, x: -12 }}
                    transition={{ duration: 0.35 }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: "8px 0",
                      fontSize: 13,
                      color: visibleSteps.includes(i) ? "rgba(226,232,240,0.7)" : "rgba(226,232,240,0.2)",
                    }}
                  >
                    <CheckCircle2
                      size={14}
                      style={{
                        color: visibleSteps.includes(i) ? "#34d399" : "rgba(255,255,255,0.1)",
                        transition: "color 0.3s",
                      }}
                    />
                    {step}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* ═══ ERROR STATE ═══ */}
          {stage === "error" && (
            <motion.div key="error" variants={fadeUp} initial="hidden" animate="visible" exit="exit" style={{ textAlign: "center", paddingTop: 48 }}>
              <div style={{ width: 56, height: 56, margin: "0 auto 20px", borderRadius: 16, background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "#f87171" }}>
                <AlertTriangle size={24} />
              </div>
              <p style={{ fontSize: 16, fontWeight: 600, color: "#f87171", margin: "0 0 8px" }}>Analysis Failed</p>
              <p style={{ fontSize: 14, color: "rgba(226,232,240,0.5)", margin: "0 0 28px", maxWidth: 400, marginLeft: "auto", marginRight: "auto" }}>
                {errorMsg}
              </p>
              <button onClick={handleReset} style={{ ...primaryBtn, display: "inline-flex", alignItems: "center", gap: 8, width: "auto" }}>
                <RotateCcw size={15} />
                Try Again
              </button>
            </motion.div>
          )}

          {/* ═══ RESULTS STATE ═══ */}
          {stage === "results" && (
            <motion.div key="results" variants={fadeUp} initial="hidden" animate="visible" exit="exit">
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr",
                  gap: 20,
                }}
              >
                {/* Responsive two-col on wider screens */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                    gap: 20,
                  }}
                >
                  {/* Left column */}
                  <div>
                    <VerdictCard verdict={verdict} />
                    <ReasonsList reasons={reasons} />
                  </div>

                  {/* Right column */}
                  <div>
                    <ScoreGauge score={score} />
                    <ConfidenceBadge confidence={confidence} />
                    <BreakdownTable breakdown={breakdown} />
                  </div>
                </div>
              </div>

              {/* Below grid */}
              <div style={{ marginTop: 32, textAlign: "center" }}>
                {user && (
                  <div style={{ marginBottom: 20 }}>
                    <p style={{ fontSize: 13, color: "#34d399", margin: "0 0 6px" }}>
                      ✓ Report saved to your dashboard
                    </p>
                    <Link
                      to="/dashboard"
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: 13,
                        fontWeight: 500,
                        color: "#a78bfa",
                        textDecoration: "none",
                        transition: "color 0.2s",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "#c4b5fd")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "#a78bfa")}
                    >
                      <LayoutDashboard size={14} />
                      View in Dashboard →
                    </Link>
                  </div>
                )}

                {reportId && (
                  <p style={{ fontSize: 12, color: "rgba(226,232,240,0.3)", margin: "0 0 24px", fontFamily: "monospace" }}>
                    Report ID: {reportId}
                  </p>
                )}

                <button onClick={handleReset} style={{ ...primaryBtn, display: "inline-flex", alignItems: "center", gap: 8, width: "auto" }}>
                  <RotateCcw size={15} />
                  Analyze Another Document
                </button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════════
   Shared styles
   ═══════════════════════════════════════════ */

const glassCard = {
  background: "rgba(255,255,255,0.03)",
  backdropFilter: "blur(20px)",
  WebkitBackdropFilter: "blur(20px)",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 16,
  padding: "20px 24px",
  marginBottom: 16,
};

const cardLabel = {
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "rgba(226,232,240,0.4)",
  margin: "0 0 12px",
};

const primaryBtn = {
  fontSize: 14,
  fontWeight: 600,
  color: "#fff",
  background: "linear-gradient(135deg, #0ea5e9, #059669)",
  border: "none",
  borderRadius: 12,
  padding: "12px 24px",
  cursor: "pointer",
  boxShadow: "0 0 20px rgba(14,165,233,0.2)",
  transition: "transform 0.2s, box-shadow 0.2s",
  fontFamily: "'Inter', system-ui, sans-serif",
};

const linkBtn = {
  background: "none",
  border: "none",
  color: "rgba(226,232,240,0.4)",
  cursor: "pointer",
  fontSize: 16,
  padding: "4px 8px",
  borderRadius: 6,
  transition: "color 0.2s",
};

export default AnalyzePage;
