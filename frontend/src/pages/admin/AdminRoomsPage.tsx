import { useCallback, useEffect, useState } from "react";
import { ApiError, api, type Room } from "../../api";

interface Draft {
  name: string;
  capacity: string;
  description: string;
}

const emptyDraft: Draft = { name: "", capacity: "0", description: "" };

export function AdminRoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [creating, setCreating] = useState<Draft>(emptyDraft);
  const [editId, setEditId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Draft>(emptyDraft);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setRooms(await api.rooms(true)); // включая архивные
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

  const create = (e: React.FormEvent) => {
    e.preventDefault();
    if (!creating.name.trim()) return;
    guard(async () => {
      await api.createRoom({
        name: creating.name.trim(),
        capacity: Number(creating.capacity) || 0,
        description: creating.description || null,
      });
      setCreating(emptyDraft);
    });
  };

  const startEdit = (r: Room) => {
    setEditId(r.id);
    setEditDraft({
      name: r.name,
      capacity: String(r.capacity),
      description: r.description ?? "",
    });
  };

  const saveEdit = () =>
    guard(async () => {
      await api.updateRoom(editId!, {
        name: editDraft.name.trim(),
        capacity: Number(editDraft.capacity) || 0,
        description: editDraft.description || null,
      });
      setEditId(null);
    });

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Комнаты</h1>
          <p className="muted">Создание, редактирование и архивирование переговорных</p>
        </div>
      </div>

      {err && <p className="error">{err}</p>}

      <section className="card">
        <h3>Добавить комнату</h3>
        <form className="inline-form" onSubmit={create}>
          <input
            placeholder="Название"
            value={creating.name}
            onChange={(e) => setCreating({ ...creating, name: e.target.value })}
            required
          />
          <input
            type="number"
            min={0}
            placeholder="Вместимость"
            value={creating.capacity}
            onChange={(e) => setCreating({ ...creating, capacity: e.target.value })}
          />
          <input
            placeholder="Описание (необязательно)"
            value={creating.description}
            onChange={(e) =>
              setCreating({ ...creating, description: e.target.value })
            }
          />
          <button type="submit">Добавить</button>
        </form>
      </section>

      <section className="card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Вместимость</th>
              <th>Описание</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rooms.map((r) =>
              editId === r.id ? (
                <tr key={r.id} className="editing">
                  <td>
                    <input
                      value={editDraft.name}
                      onChange={(e) =>
                        setEditDraft({ ...editDraft, name: e.target.value })
                      }
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      min={0}
                      value={editDraft.capacity}
                      onChange={(e) =>
                        setEditDraft({ ...editDraft, capacity: e.target.value })
                      }
                    />
                  </td>
                  <td>
                    <input
                      value={editDraft.description}
                      onChange={(e) =>
                        setEditDraft({ ...editDraft, description: e.target.value })
                      }
                    />
                  </td>
                  <td>{r.is_active ? "активна" : "архив"}</td>
                  <td className="row-actions">
                    <button className="link" onClick={saveEdit}>
                      сохранить
                    </button>
                    <button className="link muted" onClick={() => setEditId(null)}>
                      отмена
                    </button>
                  </td>
                </tr>
              ) : (
                <tr key={r.id} className={r.is_active ? "" : "archived"}>
                  <td>{r.name}</td>
                  <td>{r.capacity}</td>
                  <td className="muted">{r.description || "—"}</td>
                  <td>
                    <span className={r.is_active ? "status ok" : "status off"}>
                      {r.is_active ? "активна" : "архив"}
                    </span>
                  </td>
                  <td className="row-actions">
                    <button className="link" onClick={() => startEdit(r)}>
                      изменить
                    </button>
                    {r.is_active ? (
                      <button
                        className="link danger"
                        onClick={() => guard(() => api.archiveRoom(r.id).then(() => {}))}
                      >
                        в архив
                      </button>
                    ) : (
                      <button
                        className="link"
                        onClick={() =>
                          guard(() =>
                            api.updateRoom(r.id, { is_active: true }).then(() => {}),
                          )
                        }
                      >
                        вернуть
                      </button>
                    )}
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </section>
    </>
  );
}
