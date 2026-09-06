import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api, type Booking, type Room } from "../api";
import { useApp } from "../context";
import { AmenityChips } from "../components/Amenities";
import { TransferRequestModal } from "../components/TransferRequestModal";
import { dayBounds, fmtTime, todayStr } from "../time";

export function AvailabilityPage() {
  const { user } = useApp();
  const navigate = useNavigate();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [day, setDay] = useState(todayStr());
  const [schedule, setSchedule] = useState<Booking[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [transferFor, setTransferFor] = useState<Booking | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  useEffect(() => {
    api.rooms().then(setRooms).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    const { from, to } = dayBounds(day);
    setSchedule(await api.bookings({ date_from: from, date_to: to }));
  }, [day]);

  useEffect(() => {
    load();
  }, [load]);

  const cancel = async (id: number) => {
    setErr(null);
    try {
      await api.cancelBooking(id);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Ошибка сети");
    }
  };

  const shiftDay = (delta: number) => {
    const d = new Date(`${day}T00:00`);
    d.setDate(d.getDate() + delta);
    setDay(d.toISOString().slice(0, 10));
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Занятость комнат</h1>
          <p className="muted">Кто и когда занял переговорные</p>
        </div>
        <div className="day-nav">
          <button className="ghost" onClick={() => shiftDay(-1)}>
            ‹
          </button>
          <input
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          />
          <button className="ghost" onClick={() => shiftDay(1)}>
            ›
          </button>
          <button className="ghost" onClick={() => setDay(todayStr())}>
            сегодня
          </button>
        </div>
      </div>

      {err && <p className="error">{err}</p>}
      {okMsg && <p className="ok banner">{okMsg}</p>}

      <div className="rooms-grid">
        {rooms.map((room) => {
          const items = schedule
            .filter((b) => b.room_id === room.id)
            .sort((a, b) => a.start_time.localeCompare(b.start_time));
          return (
            <div className="card room-col" key={room.id}>
              <div className="room-col-head">
                <div>
                  <h3>{room.name}</h3>
                  <span className="muted small">до {room.capacity} чел.</span>
                </div>
                <button
                  className="ghost small"
                  onClick={() => navigate("/book", { state: { roomId: room.id } })}
                >
                  + бронь
                </button>
              </div>
              {items.length === 0 ? (
                <p className="muted empty">свободно весь день</p>
              ) : (
                items.map((b) => (
                  <div className="slot" key={b.id}>
                    <div className="slot-main">
                      <span className="slot-time">
                        {fmtTime(b.start_time)}–{fmtTime(b.end_time)}
                      </span>
                      <span className="slot-title">{b.title}</span>
                    </div>
                    {b.comment && <div className="slot-comment">{b.comment}</div>}
                    <AmenityChips ids={b.amenities} />
                    <div className="slot-actions">
                      {(b.user_id === user!.id || user!.role === "admin") && (
                        <button className="link danger" onClick={() => cancel(b.id)}>
                          отменить
                        </button>
                      )}
                      {b.user_id !== user!.id && (
                        <button className="link" onClick={() => setTransferFor(b)}>
                          запросить
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          );
        })}
      </div>

      {transferFor && (
        <TransferRequestModal
          booking={transferFor}
          onClose={() => setTransferFor(null)}
          onDone={() => {
            setTransferFor(null);
            setOkMsg("Запрос отправлен владельцу брони.");
          }}
        />
      )}
    </>
  );
}
