import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { FileText, CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { getReportStats, getReportHistory, deleteReport } from "../services/api";
import StatsCard from "../components/dashboard/StatsCard";
import HistoryTable from "../components/dashboard/HistoryTable";

/* ═══════════════════════════════════════════
   Animation helpers
   ═══════════════════════════════════════════ */

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

const stagger = {
  visible: { transition: { staggerChildren: 0.08 } },
};

/* ═══════════════════════════════════════════
   DashboardPage
   ═══════════════════════════════════════════ */

const DashboardPage = () => {
  const { user, token } = useAuth();

  /* Stats */
  const [stats, setStats] = useState({ total: 0, genuine: 0, suspicious: 0, tampered: 0 });

  /* History */
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);

  /* ── Fetch stats ── */
  useEffect(() => {
    if (!token) return;
    getReportStats()
      .then((data) => {
        setStats({
          total: data.total_reports ?? 0,
          genuine: data.genuine_count ?? 0,
          suspicious: data.suspicious_count ?? 0,
          tampered: data.tampered_count ?? 0,
        });
      })
      .catch(() => { });
  }, [token]);

  /* ── Fetch history ── */
  const loadHistory = useCallback(
    (p) => {
      if (!token) return;
      setLoading(true);
      getReportHistory(p)
        .then((data) => {
          setReports(data.reports || []);
          setTotal(data.total ?? 0);
          setPage(data.page ?? p);
          setPages(data.pages ?? 1);
        })
        .catch(() => {
          setReports([]);
        })
        .finally(() => setLoading(false));
    },
    [token],
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadHistory(1);
  }, [loadHistory]);

  /* ── Handlers ── */
  const handlePageChange = (newPage) => {
    loadHistory(newPage);
  };

  const handleDelete = async (uuid) => {
    try {
      await deleteReport(uuid);
      loadHistory(page);
      /* Also refresh stats */
      getReportStats()
        .then((data) => {
          setStats({
            total: data.total_reports ?? 0,
            genuine: data.genuine_count ?? 0,
            suspicious: data.suspicious_count ?? 0,
            tampered: data.tampered_count ?? 0,
          });
        })
        .catch(() => { });
    } catch {
      /* silently fail — ReportRow already confirmed */
    }
  };

  /* Display name */
  const displayName = user?.full_name || user?.name || user?.email || "there";

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
      <motion.div
        initial="hidden"
        animate="visible"
        variants={stagger}
        style={{ maxWidth: 1200, margin: "0 auto" }}
      >
        {/* ── Header ── */}
        <motion.div variants={fadeUp} style={{ marginBottom: 36 }}>
          <h1
            style={{
              fontFamily: "'Helvetica Now Display','Helvetica Neue',Helvetica,Arial,sans-serif",
              fontWeight: 700,
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              color: "#e5e5e5",
              margin: "0 0 8px",
            }}
          >
            Welcome back, {displayName}
          </h1>
          <p style={{ fontSize: 15, color: "rgba(229,229,229,0.5)", margin: 0 }}>
            Your document verification history
          </p>
        </motion.div>

        {/* ── Stats row ── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 16,
            marginBottom: 44,
          }}
        >
          <StatsCard
            icon={<FileText size={20} />}
            value={stats.total}
            label="Total Reports"
            color="#f59e0b"
          />
          <StatsCard
            icon={<CheckCircle size={20} />}
            value={stats.genuine}
            label="Genuine"
            color="#3fae6a"
          />
          <StatsCard
            icon={<AlertTriangle size={20} />}
            value={stats.suspicious}
            label="Suspicious"
            color="#d9a441"
          />
          <StatsCard
            icon={<XCircle size={20} />}
            value={stats.tampered}
            label="Tampered"
            color="#d95a5a"
          />
        </div>

        {/* ── History section ── */}
        <motion.div variants={fadeUp}>
          <h2
            style={{
              fontFamily: "'Helvetica Now Display','Helvetica Neue',Helvetica,Arial,sans-serif",
              fontWeight: 700,
              fontSize: 20,
              color: "#e5e5e5",
              margin: "0 0 20px",
            }}
          >
            Recent Analyses
          </h2>

          <HistoryTable
            reports={reports}
            total={total}
            page={page}
            pages={pages}
            onPageChange={handlePageChange}
            onDelete={handleDelete}
            loading={loading}
          />
        </motion.div>
      </motion.div>
    </div>
  );
};

export default DashboardPage;
