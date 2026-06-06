import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Shield,
  FileSearch,
  Zap,
  Eye,
  Check,
  ArrowRight,
  Upload,
  ScanSearch,
  BadgeCheck,
  FileText,
  Fingerprint,
  Type,
} from "lucide-react";

/* ═══════════════════════════════════════════
   Animation helpers
   ═══════════════════════════════════════════ */

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } },
};

const viewport = { once: true, amount: 0.2 };

/* ═══════════════════════════════════════════
   Keyframe injection (animated gradient bg)
   ═══════════════════════════════════════════ */

const globalKeyframes = `
@keyframes bgDrift {
  0%   { background-position: 0% 0%; }
  50%  { background-position: 100% 100%; }
  100% { background-position: 0% 0%; }
}
`;

/* ═══════════════════════════════════════════
   LandingPage
   ═══════════════════════════════════════════ */

const LandingPage = () => {
  const navigate = useNavigate();

  const scrollToHow = () => {
    const el = document.getElementById("how-it-works");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: `
          radial-gradient(ellipse 120% 80% at 30% 20%, rgba(14,165,233,0.05) 0%, transparent 60%),
          radial-gradient(ellipse 100% 60% at 70% 80%, rgba(14,165,233,0.04) 0%, transparent 50%),
          #192837
        `,
        backgroundSize: "200% 200%",
        animation: "bgDrift 25s ease-in-out infinite",
        color: "#0ea5e9",
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        overflowX: "hidden",
      }}
    >
      <style>{globalKeyframes}</style>

      {/* ────────────────────────────
          SECTION 1 — HERO
      ──────────────────────────── */}
      <motion.section
        initial="hidden"
        animate="visible"
        variants={stagger}
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "clamp(80px, 10vw, 120px) 24px 80px",
        }}
      >
        <div style={{ maxWidth: 600 }}>
          {/* Badge */}
          <motion.div variants={fadeUp}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 13,
                fontWeight: 500,
                color: "#34d399",
                background: "rgba(14,165,233,0.08)",
                border: "1px solid rgba(14,165,233,0.25)",
                borderRadius: 999,
                padding: "6px 16px",
                backdropFilter: "blur(12px)",
                marginBottom: 28,
              }}
            >
              🔍 AI-Powered Document Forensics
            </span>
          </motion.div>

          {/* Heading */}
          <motion.h1
            variants={fadeUp}
            style={{
              fontFamily:
                "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif",
              fontWeight: 700,
              fontSize: "clamp(2rem, 5vw, 3.5rem)",
              lineHeight: 1.05,
              color: "#0ea5e9",
              margin: "0 0 24px",
              letterSpacing: "-0.025em",
            }}
          >
            Verify Every Document
            <br />
            Before You{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #34d399, #0ea5e9, #059669)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Trust It
            </span>
          </motion.h1>

          {/* Subtext */}
          <motion.p
            variants={fadeUp}
            style={{
              fontSize: 16,
              lineHeight: 1.65,
              color: "rgba(226,232,240,0.7)",
              maxWidth: 520,
              margin: "0 0 36px",
            }}
          >
            AuthentIfy detects metadata tampering, pixel-level manipulation, and
            font inconsistencies in PDF documents using advanced forensic
            analysis.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={fadeUp}
            style={{ display: "flex", flexWrap: "wrap", gap: 14, marginBottom: 44 }}
          >
            <button
              onClick={() => navigate("/analyze")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 15,
                fontWeight: 600,
                color: "#ffffff",
                background: "linear-gradient(135deg, #0ea5e9, #059669)",
                border: "none",
                borderRadius: 12,
                padding: "14px 28px",
                cursor: "pointer",
                transition: "transform 0.2s, box-shadow 0.2s",
                boxShadow: "0 0 24px rgba(14,165,233,0.25)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow =
                  "0 4px 32px rgba(14,165,233,0.35)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow =
                  "0 0 24px rgba(14,165,233,0.25)";
              }}
            >
              Analyze a Document
              <ArrowRight size={16} />
            </button>

            <button
              onClick={scrollToHow}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 15,
                fontWeight: 500,
                color: "rgba(226,232,240,0.8)",
                background: "transparent",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 12,
                padding: "14px 28px",
                cursor: "pointer",
                transition: "border-color 0.2s, color 0.2s, background 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)";
                e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                e.currentTarget.style.color = "#0ea5e9";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)";
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "rgba(226,232,240,0.8)";
              }}
            >
              See How It Works
            </button>
          </motion.div>

          {/* Stats row */}
          <motion.div
            variants={fadeUp}
            style={{ display: "flex", flexWrap: "wrap", gap: 24 }}
          >
            {[
              "Multi-layer Analysis",
              "Instant Results",
              "Explainable AI",
            ].map((text) => (
              <span
                key={text}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: 13,
                  color: "rgba(226,232,240,0.55)",
                }}
              >
                <Check
                  size={15}
                  strokeWidth={2.5}
                  style={{ color: "#34d399" }}
                />
                {text}
              </span>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* ────────────────────────────
          SECTION 2 — HOW IT WORKS
      ──────────────────────────── */}
      <motion.section
        id="how-it-works"
        initial="hidden"
        whileInView="visible"
        viewport={viewport}
        variants={stagger}
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "80px 24px 96px",
        }}
      >
        <motion.h2 variants={fadeUp} style={sectionHeading}>
          How AuthentIfy Works
        </motion.h2>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 24,
            marginTop: 48,
          }}
        >
          {howSteps.map((step, i) => (
            <motion.div key={i} variants={fadeUp} style={glassCard}>
              {/* Step number */}
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: "#34d399",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: 16,
                  display: "block",
                }}
              >
                Step {i + 1}
              </span>

              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 14,
                  background: "rgba(14,165,233,0.1)",
                  border: "1px solid rgba(14,165,233,0.15)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#34d399",
                  marginBottom: 20,
                }}
              >
                {step.icon}
              </div>

              <h3
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: "#0ea5e9",
                  margin: "0 0 8px",
                }}
              >
                {step.title}
              </h3>
              <p
                style={{
                  fontSize: 14,
                  lineHeight: 1.6,
                  color: "rgba(226,232,240,0.55)",
                  margin: 0,
                }}
              >
                {step.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ────────────────────────────
          SECTION 3 — FEATURES
      ──────────────────────────── */}
      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={viewport}
        variants={stagger}
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 24px 96px",
        }}
      >
        <motion.h2 variants={fadeUp} style={sectionHeading}>
          What We Detect
        </motion.h2>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: 20,
            marginTop: 48,
          }}
        >
          {features.map((f, i) => (
            <motion.div key={i} variants={fadeUp} style={glassCard}>
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 12,
                  background: `${f.color}14`,
                  border: `1px solid ${f.color}28`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: f.color,
                  marginBottom: 18,
                }}
              >
                {f.icon}
              </div>

              <h3
                style={{
                  fontSize: 16,
                  fontWeight: 600,
                  color: "#0ea5e9",
                  margin: "0 0 6px",
                }}
              >
                {f.title}
              </h3>
              <p
                style={{
                  fontSize: 13,
                  lineHeight: 1.6,
                  color: "rgba(226,232,240,0.5)",
                  margin: 0,
                }}
              >
                {f.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ────────────────────────────
          SECTION 4 — CTA BANNER
      ──────────────────────────── */}
      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={viewport}
        variants={stagger}
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 24px 120px",
        }}
      >
        <motion.div
          variants={fadeUp}
          style={{
            position: "relative",
            borderRadius: 20,
            padding: "64px 32px",
            textAlign: "center",
            overflow: "hidden",
            background: "rgba(14,165,233,0.06)",
            border: "1px solid rgba(14,165,233,0.12)",
          }}
        >
          {/* Glow */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "radial-gradient(ellipse at center, rgba(14,165,233,0.1) 0%, transparent 70%)",
              pointerEvents: "none",
            }}
          />

          <h2
            style={{
              position: "relative",
              fontFamily:
                "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif",
              fontWeight: 700,
              fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
              color: "#0ea5e9",
              margin: "0 0 24px",
            }}
          >
            Ready to verify a document?
          </h2>

          <button
            onClick={() => navigate("/analyze")}
            style={{
              position: "relative",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              fontSize: 15,
              fontWeight: 600,
              color: "#ffffff",
              background: "linear-gradient(135deg, #0ea5e9, #059669)",
              border: "none",
              borderRadius: 12,
              padding: "14px 32px",
              cursor: "pointer",
              transition: "transform 0.2s, box-shadow 0.2s",
              boxShadow: "0 0 32px rgba(14,165,233,0.3)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow =
                "0 6px 40px rgba(14,165,233,0.45)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow =
                "0 0 32px rgba(14,165,233,0.3)";
            }}
          >
            Analyze Now
            <ArrowRight size={16} />
          </button>
        </motion.div>
      </motion.section>
    </div>
  );
};

/* ═══════════════════════════════════════════
   Shared styles
   ═══════════════════════════════════════════ */

const sectionHeading = {
  fontFamily:
    "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif",
  fontWeight: 700,
  fontSize: "clamp(1.5rem, 3vw, 2rem)",
  color: "#0ea5e9",
  margin: 0,
  textAlign: "center",
};

const glassCard = {
  background: "rgba(255,255,255,0.03)",
  backdropFilter: "blur(20px)",
  WebkitBackdropFilter: "blur(20px)",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 16,
  padding: 28,
  transition: "border-color 0.3s, background 0.3s",
};

/* ═══════════════════════════════════════════
   Data
   ═══════════════════════════════════════════ */

const howSteps = [
  {
    icon: <Upload size={22} />,
    title: "Upload PDF",
    desc: "Drag and drop your document or browse to select a PDF file for analysis.",
  },
  {
    icon: <ScanSearch size={22} />,
    title: "Deep Analysis",
    desc: "7 forensic checks run in parallel — metadata, pixel, font, signature, and more.",
  },
  {
    icon: <BadgeCheck size={22} />,
    title: "Get Verdict",
    desc: "Receive a clear verdict: Genuine, Suspicious, or Tampered — with full explainability.",
  },
];

const features = [
  {
    icon: <Shield size={20} />,
    title: "Metadata Tampering",
    desc: "Detects altered creation dates, author fields, and producer mismatches.",
    color: "#34d399",
  },
  {
    icon: <Eye size={20} />,
    title: "ELA Pixel Analysis",
    desc: "Error Level Analysis reveals pixel-level edits invisible to the naked eye.",
    color: "#60a5fa",
  },
  {
    icon: <Type size={20} />,
    title: "Font Inconsistency",
    desc: "Identifies mixed or substituted fonts that signal document splicing.",
    color: "#fbbf24",
  },
  {
    icon: <Fingerprint size={20} />,
    title: "Digital Signature",
    desc: "Validates cryptographic signatures and flags broken or missing seals.",
    color: "#a78bfa",
  },
  {
    icon: <FileSearch size={20} />,
    title: "OCR Anomalies",
    desc: "Spots text layers that don't match rendered content or overlay misalignment.",
    color: "#f87171",
  },
  {
    icon: <FileText size={20} />,
    title: "Template Matching",
    desc: "Compares against known document templates to detect structural deviations.",
    color: "#2dd4bf",
  },
];

export default LandingPage;