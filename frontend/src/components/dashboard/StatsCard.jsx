import { motion } from "framer-motion";

const StatsCard = ({ icon, value, label, color, trend }) => {
  const iconBg = color ? `${color}18` : "rgba(255,255,255,0.08)";
  const iconColor = color || "#ffffff";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] }}
      style={{
        background: "rgba(255, 255, 255, 0.04)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: 16,
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: "50%",
          background: iconBg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: iconColor,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>

      {/* Value */}
      <span
        style={{
          fontFamily: "'Helvetica Now Display', 'Helvetica Neue', Helvetica, Arial, sans-serif",
          fontWeight: 700,
          fontSize: 36,
          lineHeight: 1.1,
          color: "#ffffff",
          letterSpacing: "-0.02em",
        }}
      >
        {value}
      </span>

      {/* Label + Trend */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            fontSize: 14,
            color: "rgba(255, 255, 255, 0.5)",
            fontWeight: 400,
            lineHeight: 1.4,
          }}
        >
          {label}
        </span>

        {trend && (
          <span
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: "#34d399",
              background: "rgba(52, 211, 153, 0.1)",
              borderRadius: 6,
              padding: "2px 8px",
              whiteSpace: "nowrap",
            }}
          >
            {trend}
          </span>
        )}
      </div>
    </motion.div>
  );
};

export default StatsCard;
