import { useCallback, useEffect, useState } from "react";
import { ApiError, api, type AdminUser } from "../../api";
import { useApp } from "../../context";
import { fmtDateTime } from "../../time";

export function AdminUsersPage() {
  const { user: me } = useApp();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setUsers(await api.users());
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const guard = async (fn: () => Promise<void>) => {
    setErr(null);
    try {
      await fn();
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Ошибка сети");
    }
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Пользователи</h1>
          <p className="muted">Роли и доступ сотрудников</p>
        </div>
      </div>

      {err && <p className="error">{err}</p>}

      <section className="card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Броней</th>
              <th>Статус</th>
              <th>Регистрация</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = u.id === me!.id;
              return (
                <tr key={u.id} className={u.is_active ? "" : "archived"}>
                  <td>
                    {u.full_name}
                    {isSelf && <span className="badge subtle">вы</span>}
                  </td>
                  <td className="muted">{u.email}</td>
                  <td>
                    <span className={u.role === "admin" ? "status admin" : "status"}>
                      {u.role}
                    </span>
                  </td>
                  <td>{u.bookings_count}</td>
                  <td>
                    <span className={u.is_active ? "status ok" : "status off"}>
                      {u.is_active ? "активен" : "заблокирован"}
                    </span>
                  </td>
                  <td className="muted small">{fmtDateTime(u.created_at)}</td>
                  <td className="row-actions">
                    {isSelf ? (
                      <span className="muted small">—</span>
                    ) : (
                      <>
                        <button
                          className="link"
                          onClick={() =>
                            guard(() =>
                              api
                                .updateUser(u.id, {
                                  role: u.role === "admin" ? "user" : "admin",
                                })
                                .then(() => {}),
                            )
                          }
                        >
                          {u.role === "admin" ? "снять админа" : "сделать админом"}
                        </button>
                        <button
                          className={u.is_active ? "link danger" : "link"}
                          onClick={() =>
                            guard(() =>
                              api
                                .updateUser(u.id, { is_active: !u.is_active })
                                .then(() => {}),
                            )
                          }
                        >
                          {u.is_active ? "заблокировать" : "разблокировать"}
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </>
  );
}
