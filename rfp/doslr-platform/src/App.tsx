import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { ReactElement } from "react";
import LoginPage from "./pages/LoginPage";
import MapWorkbenchPage from "./pages/MapWorkbenchPage";
import NilamMobilePage from "./pages/NilamMobilePage";
import NilAiPage from "./pages/NilAiPage";
import ReportsPage from "./pages/ReportsPage";
import WorkflowDemoPage from "./pages/workflows/WorkflowDemoPage";
import NotFoundPage from "./pages/NotFoundPage";
import { isAuthenticated } from "./lib/auth";

function ProtectedRoute({ children }: { children: ReactElement }) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <MapWorkbenchPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/mobile"
        element={
          <ProtectedRoute>
            <NilamMobilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/nil-ai"
        element={
          <ProtectedRoute>
            <NilAiPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/:id"
        element={
          <ProtectedRoute>
            <WorkflowDemoPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
