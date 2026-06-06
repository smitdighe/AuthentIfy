import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ShieldCheck, LogOut, LayoutDashboard, Menu, X } from "lucide-react";
import { useState } from "react";

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
    setOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  const navLink = (to, label) => (
    <Link
      to={to}
      onClick={() => setOpen(false)}
      style={{
        fontSize: 14,
        fontWeight: 500,
        color: isActive(to) ? "#13364dff" : "rgba(226,232,240,0.65)",
        textDecoration: "none",
        transition: "color 0.2s",
        padding: "6px 0",
      }}
      onMouseEnter={(e) => { if (!isActive(to)) e.currentTarget.style.color = "#0ea5e9"; }}
      onMouseLeave={(e) => { if (!isActive(to)) e.currentTarget.style.color = "rgba(226,232,240,0.65)"; }}
    >
      {label}
    </Link>
  );

  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        height: 64,
        background: "rgba(14, 55, 81, 0.69)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          height: "100%",
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Logo */}
        <Link
          to="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            textDecoration: "none",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 9,
              background: "linear-gradient(135deg, #0ea5e9, #059669)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ShieldCheck size={16} color="#fff" />
          </div>
          <span
            style={{
              fontFamily: "'Helvetica Now Display','Helvetica Neue',Helvetica,Arial,sans-serif",
              fontWeight: 700,
              fontSize: 17,
              color: "#0ea5e9",
            }}
          >
            AuthentIfy
          </span>
        </Link>

        {/* Desktop links */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 28,
          }}
          className="nav-desktop"
        >
          {navLink("/analyze", "Analyze")}
          {user && navLink("/dashboard", "Dashboard")}
          {!user ? (
            <>
              {navLink("/login", "Login")}
              <Link
                to="/register"
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#fff",
                  background: "linear-gradient(135deg, #0ea5e9, #059669)",
                  borderRadius: 10,
                  padding: "8px 18px",
                  textDecoration: "none",
                  transition: "box-shadow 0.2s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 0 20px rgba(14,165,233,0.3)")}
                onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
              >
                Get Started
              </Link>
            </>
          ) : (
            <button
              onClick={handleLogout}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                fontSize: 13,
                fontWeight: 500,
                color: "rgba(226,232,240,0.55)",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 10,
                padding: "7px 14px",
                cursor: "pointer",
                transition: "border-color 0.2s, color 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#f87171";
                e.currentTarget.style.borderColor = "rgba(248,113,113,0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "rgba(226,232,240,0.55)";
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
              }}
            >
              <LogOut size={14} />
              Logout
            </button>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setOpen((v) => !v)}
          className="nav-mobile-toggle"
          style={{
            display: "none",
            background: "none",
            border: "none",
            color: "rgba(226,232,240,0.7)",
            cursor: "pointer",
            padding: 4,
          }}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div
          style={{
            position: "absolute",
            top: 64,
            left: 0,
            right: 0,
            background: "rgba(176, 210, 210,0.97)",
            backdropFilter: "blur(20px)",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            padding: "16px 24px 20px",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            zIndex: 99,
          }}
          className="nav-mobile-drawer"
        >
          {navLink("/analyze", "Analyze")}
          {user && navLink("/dashboard", "Dashboard")}
          {!user ? (
            <>
              {navLink("/login", "Login")}
              {navLink("/register", "Register")}
            </>
          ) : (
            <button
              onClick={handleLogout}
              style={{
                fontSize: 14,
                fontWeight: 500,
                color: "#f87171",
                background: "none",
                border: "none",
                cursor: "pointer",
                textAlign: "left",
                padding: "6px 0",
              }}
            >
              Logout
            </button>
          )}
        </div>
      )}

      {/* Responsive CSS */}
      <style>{`
        @media (max-width: 640px) {
          .nav-desktop { display: none !important; }
          .nav-mobile-toggle { display: flex !important; }
        }
      `}</style>
    </nav>
  );
};

export default Navbar;
