import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { User, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

/* ═══════════════════════════════════════════
   Shared input styles (mirrors LoginPage)
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

const inputError = {
  ...inputBase,
  borderColor: "rgba(248,113,113,0.5)",
};

const iconWrap = {
  position: "absolute",
  left: 14,
  top: 17,
  color: "rgba(229,229,229,0.35)",
  pointerEvents: "none",
  display: "flex",
};

const fieldError = {
  fontSize: 12,
  color: "#f87171",
  marginTop: 6,
  lineHeight: 1.3,
};

/* ═══════════════════════════════════════════
   Validation helpers
   ═══════════════════════════════════════════ */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const validate = ({ email, password, confirmPw }) => {
  const e = {};
  if (email && !EMAIL_RE.test(email)) e.email = "Enter a valid email address";
  if (password && password.length < 8)
    e.password = "Password must be at least 8 characters";
  if (confirmPw && password && confirmPw !== password)
    e.confirmPw = "Passwords do not match";
  return e;
};

/* ═══════════════════════════════════════════
   RegisterPage
   ═══════════════════════════════════════════ */

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, user, loading: authLoading } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showCpw, setShowCpw] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState({});

  /* Redirect if already logged in */
  useEffect(() => {
    if (!authLoading && user) navigate("/analyze", { replace: true });
  }, [authLoading, user, navigate]);

  /* Live validation on touched fields */
  useEffect(() => {
    const next = validate({ email, password, confirmPw });
    // only show errors for touched fields
    const filtered = {};
    Object.keys(next).forEach((k) => {
      if (touched[k]) filtered[k] = next[k];
    });
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setErrors(filtered);
  }, [email, password, confirmPw, touched]);

  const touch = (field) =>
    setTouched((t) => ({ ...t, [field]: true }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");

    /* Full validation pass */
    const allErrors = validate({ email, password, confirmPw });
    if (!EMAIL_RE.test(email)) allErrors.email = "Enter a valid email address";
    if (!password) allErrors.password = "Password is required";
    if (!confirmPw) allErrors.confirmPw = "Please confirm your password";

    if (Object.keys(allErrors).length > 0) {
      setErrors(allErrors);
      setTouched({ email: true, password: true, confirmPw: true });
      return;
    }

    setLoading(true);
    try {
      // Context signature is register(email, password, fullName) — pass in
      // that order; register() resolves to { success, error }, never throws.
      const result = await register(email, password, name || undefined);
      if (result?.success) {
        navigate("/analyze", { replace: true });
      } else {
        setApiError(result?.error || "Registration failed");
      }
    } catch (err) {
      setApiError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const disabled = loading || authLoading;

  const focusBorder = (e) =>
    (e.currentTarget.style.borderColor = "#f59e0b");
  const blurBorder = (e) =>
    (e.currentTarget.style.borderColor = "rgba(229,229,229,0.15)");

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
        <div style={{ textAlign: "center", marginBottom: 36 }}>
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
            Create Account
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "rgba(229,229,229,0.45)",
              margin: 0,
            }}
          >
            Start verifying documents today
          </p>
        </div>

        {/* ── Form ── */}
        <form onSubmit={handleSubmit} noValidate>
          {/* Full Name (optional) */}
          <div style={{ position: "relative", marginBottom: 16 }}>
            <div style={iconWrap}>
              <User size={16} />
            </div>
            <input
              type="text"
              placeholder="Full Name (optional)"
              disabled={disabled}
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={inputBase}
              onFocus={focusBorder}
              onBlur={blurBorder}
            />
          </div>

          {/* Email */}
          <div style={{ position: "relative", marginBottom: errors.email ? 4 : 16 }}>
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
              onBlur={() => {
                touch("email");
                blurBorder({ currentTarget: document.activeElement?.previousSibling });
              }}
              onFocus={focusBorder}
              style={errors.email ? inputError : inputBase}
            />
            {errors.email && <p style={fieldError}>{errors.email}</p>}
          </div>

          {/* Password */}
          <div
            style={{
              position: "relative",
              marginBottom: errors.password ? 4 : 16,
            }}
          >
            <div style={iconWrap}>
              <Lock size={16} />
            </div>
            <input
              type={showPw ? "text" : "password"}
              placeholder="Password (min 8 chars)"
              required
              disabled={disabled}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => touch("password")}
              onFocus={focusBorder}
              style={{
                ...(errors.password ? inputError : inputBase),
                paddingRight: 44,
              }}
            />
            <button
              type="button"
              tabIndex={-1}
              onClick={() => setShowPw((v) => !v)}
              style={toggleBtn}
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
            {errors.password && <p style={fieldError}>{errors.password}</p>}
          </div>

          {/* Confirm Password */}
          <div
            style={{
              position: "relative",
              marginBottom: errors.confirmPw ? 4 : 24,
            }}
          >
            <div style={iconWrap}>
              <Lock size={16} />
            </div>
            <input
              type={showCpw ? "text" : "password"}
              placeholder="Confirm Password"
              required
              disabled={disabled}
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              onBlur={() => touch("confirmPw")}
              onFocus={focusBorder}
              style={{
                ...(errors.confirmPw ? inputError : inputBase),
                paddingRight: 44,
              }}
            />
            <button
              type="button"
              tabIndex={-1}
              onClick={() => setShowCpw((v) => !v)}
              style={toggleBtn}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "rgba(229,229,229,0.7)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "rgba(229,229,229,0.35)")
              }
              aria-label={showCpw ? "Hide password" : "Show password"}
            >
              {showCpw ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
            {errors.confirmPw && <p style={fieldError}>{errors.confirmPw}</p>}
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
            {loading ? "Creating account…" : "Create Account"}
          </button>

          {/* API error */}
          {apiError && (
            <p
              style={{
                marginTop: 16,
                fontSize: 13,
                color: "#f87171",
                textAlign: "center",
                lineHeight: 1.4,
              }}
            >
              {apiError}
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
          Already have an account?{" "}
          <Link
            to="/login"
            style={{
              color: "#f59e0b",
              textDecoration: "none",
              fontWeight: 500,
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#fbbf24")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#f59e0b")}
          >
            Login →
          </Link>
        </p>
      </motion.div>
    </div>
  );
};

/* ═══════════════════════════════════════════
   Shared small styles
   ═══════════════════════════════════════════ */

const toggleBtn = {
  position: "absolute",
  right: 12,
  top: 17,
  background: "none",
  border: "none",
  padding: 4,
  cursor: "pointer",
  color: "rgba(229,229,229,0.35)",
  display: "flex",
  transition: "color 0.2s",
};

export default RegisterPage;
