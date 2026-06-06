import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

const Footer = () => (
  <footer
    style={{
      background: "rgba(176, 210, 210,0.6)",
      borderTop: "1px solid rgba(255,255,255,0.04)",
      padding: "32px 24px",
      fontFamily: "'Inter', system-ui, sans-serif",
    }}
  >
    <div
      style={{
        maxWidth: 1280,
        margin: "0 auto",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 16,
      }}
    >
      {/* Left */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <ShieldCheck size={14} style={{ color: "#34d399" }} />
        <span style={{ fontSize: 13, color: "rgba(226,232,240,0.35)" }}>
          © {new Date().getFullYear()} AuthentIfy. All rights reserved.
        </span>
      </div>

      {/* Right */}
      <div style={{ display: "flex", gap: 20 }}>
        {[
          { to: "/analyze", label: "Analyze" },
          { to: "/login", label: "Login" },
          { to: "/register", label: "Register" },
        ].map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            style={{
              fontSize: 13,
              color: "rgba(226,232,240,0.3)",
              textDecoration: "none",
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(226,232,240,0.6)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(226,232,240,0.3)")}
          >
            {label}
          </Link>
        ))}
      </div>
    </div>
  </footer>
);

export default Footer;
