import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeOff, Mail, Lock } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

/* ═══════════════════════════════════════════
   Shared input style builder
   ═══════════════════════════════════════════ */

const inputBase = {
  width: "100%",
  boxSizing: "border-box",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(229,229,229,0.15)",
  borderRadius: 12,
  padding: "14px 16px 14px 44px",
  fontSize: 14,
  color: "#e5e5e5",
  outline: "none",
  transition: "border-color 0.2s",
  fontFamily: "'Inter', system-ui, sans-serif",
};

const iconWrap = {
  position: "absolute",
  left: 14,
  top: "50%",
  transform: "translateY(-50%)",
  color: "rgba(229,229,229,0.35)",
  pointerEvents: "none",
  display: "flex",
};

/* ═══════════════════════════════════════════
   LoginPage
   ═══════════════════════════════════════════ */

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, user, loading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /* Redirect if already logged in */
  useEffect(() => {
    if (!authLoading && user) navigate("/analyze", { replace: true });
  }, [authLoading, user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // login() resolves to { success, error } — it never throws.
      const result = await login(email, password);
      if (result?.success) {
        navigate("/analyze", { replace: true });
      } else {
        setError(result?.error || "Login failed. Check your credentials.");
      }
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const disabled = loading || authLoading;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "transparent",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] }}
        style={{
          width: "100%",
          maxWidth: 420,
          background: "rgba(18,18,20,0.5)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border: "1px solid rgba(245,158,11,0.15)",
          borderRadius: 20,
          padding: 40,
        }}
      >
        {/* ── Logo + heading ── */}
        <div
          style={{
            textAlign: "center",
            marginBottom: 36,
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              margin: "0 auto 16px",
              borderRadius: 14,
              background: "#f59e0b",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 28px rgba(245,158,11,0.25)",
            }}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#fff"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>

          <h1
            style={{
              fontFamily:
                "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif",
              fontWeight: 700,
              fontSize: 24,
              color: "#f59e0b",
              margin: "0 0 6px",
            }}
          >
            AuthentIfy
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "rgba(229,229,229,0.45)",
              margin: 0,
            }}
          >
            Verify before you trust
          </p>
        </div>

        {/* ── Form ── */}
        <form onSubmit={handleSubmit}>
          {/* Email */}
          <div style={{ position: "relative", marginBottom: 16 }}>
            <div style={iconWrap}>
              <Mail size={16} />
            </div>
            <input
              type="email"
              placeholder="Email address"
              required
              disabled={disabled}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputBase}
              onFocus={(e) =>
                (e.currentTarget.style.borderColor = "#f59e0b")
              }
              onBlur={(e) =>
              (e.currentTarget.style.borderColor =
                "rgba(229,229,229,0.15)")
              }
            />
          </div>

          {/* Password */}
          <div style={{ position: "relative", marginBottom: 24 }}>
            <div style={iconWrap}>
              <Lock size={16} />
            </div>
            <input
              type={showPw ? "text" : "password"}
              placeholder="Password"
              required
              disabled={disabled}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ ...inputBase, paddingRight: 44 }}
              onFocus={(e) =>
                (e.currentTarget.style.borderColor = "#f59e0b")
              }
              onBlur={(e) =>
              (e.currentTarget.style.borderColor =
                "rgba(229,229,229,0.15)")
              }
            />
            <button
              type="button"
              tabIndex={-1}
              onClick={() => setShowPw((v) => !v)}
              style={{
                position: "absolute",
                right: 12,
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                padding: 4,
                cursor: "pointer",
                color: "rgba(229,229,229,0.35)",
                display: "flex",
                transition: "color 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "rgba(229,229,229,0.7)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "rgba(229,229,229,0.35)")
              }
              aria-label={showPw ? "Hide password" : "Show password"}
            >
              {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={disabled}
            style={{
              width: "100%",
              padding: "14px 24px",
              fontSize: 15,
              fontWeight: 600,
              color: "#fff",
              background: disabled
                ? "rgba(245,158,11,0.35)"
                : "#f59e0b",
              border: "none",
              borderRadius: 12,
              cursor: disabled ? "not-allowed" : "pointer",
              transition: "transform 0.2s, box-shadow 0.2s, opacity 0.2s",
              boxShadow: disabled
                ? "none"
                : "0 0 24px rgba(245,158,11,0.2)",
              fontFamily: "'Inter', system-ui, sans-serif",
            }}
            onMouseEnter={(e) => {
              if (!disabled) {
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.boxShadow =
                  "0 4px 28px rgba(245,158,11,0.35)";
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled) {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow =
                  "0 0 24px rgba(245,158,11,0.2)";
              }
            }}
          >
            {loading ? "Signing in…" : "Login"}
          </button>

          {/* Error */}
          {error && (
            <p
              style={{
                marginTop: 16,
                fontSize: 13,
                color: "#f87171",
                textAlign: "center",
                lineHeight: 1.4,
              }}
            >
              {error}
            </p>
          )}
        </form>

        {/* ── Bottom link ── */}
        <p
          style={{
            marginTop: 28,
            fontSize: 13,
            color: "rgba(229,229,229,0.45)",
            textAlign: "center",
          }}
        >
          Don't have an account?{" "}
          <Link
            to="/register"
            style={{
              color: "#f59e0b",
              textDecoration: "none",
              fontWeight: 500,
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#fbbf24")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#f59e0b")}
          >
            Register →
          </Link>
        </p>
      </motion.div>
    </div>
  );
};

export default LoginPage;
