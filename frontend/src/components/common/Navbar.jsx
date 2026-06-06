import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Shield, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const navLinks = [
  { label: 'Home', path: '/' },
  { label: 'Analyze', path: '/analyze' },
];

const authNavLinks = [
  { label: 'Home', path: '/' },
  { label: 'Analyze', path: '/analyze' },
  { label: 'Dashboard', path: '/dashboard' },
];

const linkVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, duration: 0.35, ease: 'easeOut' },
  }),
};

const sheetVariants = {
  closed: { x: '100%' },
  open: { x: 0, transition: { duration: 0.35, ease: [0.25, 1, 0.5, 1] } },
  exit: { x: '100%', transition: { duration: 0.25, ease: 'easeIn' } },
};

const backdropVariants = {
  closed: { opacity: 0 },
  open: { opacity: 1, transition: { duration: 0.25 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

/**
 * Main navigation bar for AuthentIfy.
 * Sticky, glassmorphic header with responsive mobile sheet menu.
 *
 * @returns {JSX.Element}
 */
export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, isAuth, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const links = isAuth ? authNavLinks : navLinks;

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  function handleLogout() {
    setMobileOpen(false);
    logout();
  }

  function truncateEmail(email) {
    if (!email) return '';
    return email.length > 22 ? email.slice(0, 19) + '...' : email;
  }

  return (
    <nav
      className="sticky top-0 z-50 flex items-center justify-between px-6 lg:px-10"
      style={{
        height: 64,
        background: 'rgba(176, 210, 210,0.95)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(226,232,240,0.08)',
      }}
    >
      {/* ── Left: Logo ── */}
      <Link to="/" className="flex items-center gap-2.5 group">
        <div
          className="flex items-center justify-center rounded-lg"
          style={{
            width: 34,
            height: 34,
            background: '#0ea5e9',
          }}
        >
          <span
            className="font-heading text-base font-bold leading-none"
            style={{ color: '#192837' }}
          >
            A
          </span>
        </div>
        <span className="font-heading text-lg text-auth-silver tracking-tight hidden sm:block">
          AuthentIfy
        </span>
      </Link>

      {/* ── Center: Desktop Links ── */}
      <div className="hidden md:flex items-center gap-8">
        {links.map((link, i) => (
          <motion.div
            key={link.path}
            custom={i}
            initial="hidden"
            animate="visible"
            variants={linkVariants}
          >
            <Link
              to={link.path}
              className="text-sm font-medium transition-colors duration-200"
              style={{
                color:
                  location.pathname === link.path
                    ? '#0ea5e9'
                    : 'rgba(226,232,240,0.7)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#0ea5e9')}
              onMouseLeave={(e) =>
              (e.currentTarget.style.color =
                location.pathname === link.path
                  ? '#0ea5e9'
                  : 'rgba(226,232,240,0.7)')
              }
            >
              {link.label}
            </Link>
          </motion.div>
        ))}
      </div>

      {/* ── Right: Auth Actions (Desktop) ── */}
      <div className="hidden md:flex items-center gap-3">
        {!isAuth ? (
          <>
            <Link
              to="/login"
              className="btn-outline text-sm px-5 py-2"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="btn-primary text-sm px-5 py-2"
            >
              Get Started
            </Link>
          </>
        ) : (
          <div className="flex items-center gap-4">
            <span
              className="text-sm hidden lg:block"
              style={{ color: 'rgba(226,232,240,0.6)' }}
            >
              {truncateEmail(user?.email)}
            </span>
            <Link
              to="/dashboard"
              className="flex items-center gap-1.5 text-sm font-medium transition-colors duration-200"
              style={{ color: 'rgba(226,232,240,0.7)' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#0ea5e9')}
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = 'rgba(226,232,240,0.7)')
              }
            >
              <Shield size={15} />
              Dashboard
            </Link>
            <button
              onClick={handleLogout}
              className="btn-outline text-sm px-4 py-2 flex items-center gap-1.5"
            >
              <LogOut size={14} />
              Logout
            </button>
          </div>
        )}
      </div>

      {/* ── Hamburger (Mobile) ── */}
      <button
        className="md:hidden flex items-center justify-center"
        onClick={() => setMobileOpen((prev) => !prev)}
        aria-label="Toggle menu"
        style={{ color: '#0ea5e9' }}
      >
        {mobileOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* ── Mobile Sheet ── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              key="backdrop"
              variants={backdropVariants}
              initial="closed"
              animate="open"
              exit="exit"
              className="fixed inset-0 z-40 md:hidden"
              style={{ background: 'rgba(176, 210, 210,0.5)' }}
              onClick={() => setMobileOpen(false)}
            />

            {/* Sheet */}
            <motion.div
              key="sheet"
              variants={sheetVariants}
              initial="closed"
              animate="open"
              exit="exit"
              className="fixed top-0 right-0 bottom-0 z-50 w-72 flex flex-col md:hidden"
              style={{
                background: '#192837',
                borderLeft: '1px solid rgba(226,232,240,0.1)',
              }}
            >
              {/* Sheet Header */}
              <div
                className="flex items-center justify-between px-6"
                style={{
                  height: 64,
                  borderBottom: '1px solid rgba(226,232,240,0.08)',
                }}
              >
                <span className="font-heading text-lg text-auth-silver">
                  Menu
                </span>
                <button
                  onClick={() => setMobileOpen(false)}
                  aria-label="Close menu"
                  style={{ color: '#0ea5e9' }}
                >
                  <X size={22} />
                </button>
              </div>

              {/* Sheet Links */}
              <div className="flex flex-col gap-1 px-4 py-6 flex-1">
                {links.map((link, i) => (
                  <motion.div
                    key={link.path}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{
                      opacity: 1,
                      y: 0,
                      transition: { delay: 0.1 + i * 0.07, duration: 0.3 },
                    }}
                  >
                    <Link
                      to={link.path}
                      className="block rounded-xl px-4 py-3 text-sm font-medium transition-colors duration-200"
                      style={{
                        color:
                          location.pathname === link.path
                            ? '#0ea5e9'
                            : 'rgba(226,232,240,0.7)',
                        background:
                          location.pathname === link.path
                            ? 'rgba(14,165,233,0.08)'
                            : 'transparent',
                      }}
                    >
                      {link.label}
                    </Link>
                  </motion.div>
                ))}

                {isAuth && (
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{
                      opacity: 1,
                      y: 0,
                      transition: { delay: 0.1 + links.length * 0.07, duration: 0.3 },
                    }}
                    className="mt-2 px-4"
                  >
                    <span
                      className="text-xs block truncate"
                      style={{ color: 'rgba(226,232,240,0.45)' }}
                    >
                      {user?.email}
                    </span>
                  </motion.div>
                )}
              </div>

              {/* Sheet CTA */}
              <div
                className="px-5 pb-8 flex flex-col gap-3"
                style={{ borderTop: '1px solid rgba(226,232,240,0.08)', paddingTop: 20 }}
              >
                {!isAuth ? (
                  <>
                    <Link
                      to="/login"
                      className="btn-outline text-sm text-center py-3"
                      onClick={() => setMobileOpen(false)}
                    >
                      Login
                    </Link>
                    <Link
                      to="/register"
                      className="btn-primary text-sm text-center py-3"
                      onClick={() => setMobileOpen(false)}
                    >
                      Get Started
                    </Link>
                  </>
                ) : (
                  <button
                    onClick={handleLogout}
                    className="btn-outline text-sm py-3 flex items-center justify-center gap-2"
                  >
                    <LogOut size={15} />
                    Logout
                  </button>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </nav>
  );
}
