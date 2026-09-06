import { useCallback, useEffect, useState } from "react";
import { ApiError, api, type AdminBooking, type Room } from "../../api";
import { AmenityChips } from "../../components/Amenities";
import { dayKey, fmtDayLong, fmtTime } from "../../time";

export function AdminBookingsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [bookings, setBookings] = useState<AdminBooking[]>([]);
  const [roomId, setRoomId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.rooms(true).then(setRooms).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      // Даты фильтра — локальная полночь -> ISO; to включительно (+1 день).
      const params: { room_id?: number; date_from?: string; date_to?: string } = {};
      if (roomId) params.room_id = Number(roomId);
      if (from) params.date_from = new Date(`${from}T00:00`).toISOString();
      if (to) {
        const d = new Date(`${to}T00:00`);
        d.setDate(d.getDate() + 1);
        params.date_to = d.toISOString();
      }
      setBookings(await api.adminBookings(params));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Ошибка сети");
    } finally {
      setLoading(false);
    }
  }, [roomId, from, to]);

  useEffect(() => {
    load();
  }, [load]);

  // Группировка по дате (брони уже отсортированы от новых к старым).
  const groups: { key: string; iso: string; items: AdminBooking[] }[] = [];
  for (const b of bookings) {
    const key = dayKey(b.start_time);
    const last = groups[groups.length - 1];
    if (last && last.key === key) last.items.push(b);
    else groups.push({ key, iso: b.start_time, items: [b] });
  }

  const reset = () => {
    setRoomId("");
    setFrom("");
    setTo("");
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>История броней</h1>
          <p className="muted">Все брони по датам со всеми характеристиками</p>
        </div>
      </div>

      <section className="card filters">
        <label>
          Комната
          <select value={roomId} onChange={(e) => setRoomId(e.target.value)}>
            <option value="">все</option>
            {rooms.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          С даты
          <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label>
          По дату
          <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </label>
        <button className="ghost" onClick={reset}>
          сбросить
        </button>
      </section>

      {err && <p className="error">{err}</p>}

      {loading ? (
        <p className="muted">Загрузка…</p>
      ) : groups.length === 0 ? (
        <div className="card empty-state">
          <p>Броней по фильтру нет.</p>
        </div>
      ) : (
        groups.map((g) => (
          <div className="date-group" key={g.key}>
            <div className="date-header">
              <span>{fmtDayLong(g.iso)}</span>
              <span className="muted small">{g.items.length} бронь(и)</span>
            </div>
            <div className="card">
              <table className="admin-table history">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>Комната</th>
                    <th>Автор</th>
                    <th>Тема</th>
                    <th>Комментарий</th>
                    <th>Допы</th>
                  </tr>
                </thead>
                <tbody>
                  {g.items.map((b) => (
                    <tr key={b.id}>
                      <td className="nowrap slot-time">
                        {fmtTime(b.start_time)}–{fmtTime(b.end_time)}
                      </td>
                      <td>{b.room_name}</td>
                      <td>
                        <div>{b.user.full_name}</div>
                        <div className="muted small">{b.user.email}</div>
                      </td>
                      <td>{b.title}</td>
                      <td className="muted">{b.comment || "—"}</td>
                      <td>
                        {b.amenities.length ? (
                          <AmenityChips ids={b.amenities} />
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </>
  );
}
