import { NavLink, Outlet } from "react-router-dom";
import { useApp } from "../context";

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "nav-link active" : "nav-link";

export function Layout() {
  const { user, logout } = useApp();
  const isAdmin = user?.role === "admin";

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <span className="brand">AiSpace</span>
          <nav className="nav">
            <NavLink to="/" end className={navClass}>
              Занятость
            </NavLink>
            <NavLink to="/book" className={navClass}>
              Забронировать
            </NavLink>
            <NavLink to="/my" className={navClass}>
              Мои брони
            </NavLink>
            {isAdmin && (
              <>
                <span className="nav-sep" />
                <NavLink to="/admin/rooms" className={navClass}>
                  Комнаты
                </NavLink>
                <NavLink to="/admin/users" className={navClass}>
                  Пользователи
                </NavLink>
                <NavLink to="/admin/bookings" className={navClass}>
                  История
                </NavLink>
                <NavLink to="/admin/analytics" className={navClass}>
                  Аналитика
                </NavLink>
              </>
            )}
          </nav>
        </div>
        <span className="userbox">
          {user?.full_name}
          {isAdmin && <span className="badge">admin</span>}
          <button className="link" onClick={logout}>
            выйти
          </button>
        </span>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
