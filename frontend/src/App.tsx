import { Navigate, Route, Routes } from "react-router-dom";
import { useApp } from "./context";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { AvailabilityPage } from "./pages/AvailabilityPage";
import { BookPage } from "./pages/BookPage";
import { MyBookingsPage } from "./pages/MyBookingsPage";
import { AdminRoomsPage } from "./pages/admin/AdminRoomsPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { AdminBookingsPage } from "./pages/admin/AdminBookingsPage";
import { AnalyticsPage } from "./pages/admin/AnalyticsPage";

export function App() {
  const { user, loading } = useApp();

  if (loading) return <div className="center muted">Загрузка…</div>;

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const isAdmin = user.role === "admin";

  return (
    <Routes>
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route element={<Layout />}>
        <Route path="/" element={<AvailabilityPage />} />
        <Route path="/book" element={<BookPage />} />
        <Route path="/my" element={<MyBookingsPage />} />
        {isAdmin ? (
          <>
            <Route path="/admin/rooms" element={<AdminRoomsPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/bookings" element={<AdminBookingsPage />} />
            <Route path="/admin/analytics" element={<AnalyticsPage />} />
          </>
        ) : null}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
