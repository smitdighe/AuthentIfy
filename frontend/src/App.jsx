import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";

import LandingPage from "./pages/LandingPage";
import AnalyzePage from "./pages/AnalyzePage";
import ReportPage from "./pages/ReportPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";

const App = () => (
  <AuthProvider>
    <Navbar />
    <main style={{ minHeight: "calc(100vh - 64px)" }}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/analyze"
          element={
            <ProtectedRoute>
              <AnalyzePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/report/:reportId"
          element={
            <ProtectedRoute>
              <ReportPage />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
    <Footer />
  </AuthProvider>
);

export default App;
