import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ApiError, api, type Booking, type Room } from "../api";
import { AmenityChips } from "../components/Amenities";
import { fmtDateRange } from "../time";

export function MyBookingsPage() {
  const location = useLocation();
  const justBooked = (location.state as { justBooked?: boolean } | null)?.justBooked;
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [rooms, setRooms] = useState<Record<number, Room>>({});
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const [b, r] = await Promise.all([api.myBookings(), api.rooms(true)]);
    setBookings(b);
    setRooms(Object.fromEntries(r.map((x) => [x.id, x])));
    setLoading(false);
  }, []);

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

  const now = new Date().toISOString();
  const upcoming = bookings
    .filter((b) => b.end_time >= now)
    .sort((a, b) => a.start_time.localeCompare(b.start_time));
  const past = bookings
    .filter((b) => b.end_time < now)
    .sort((a, b) => b.start_time.localeCompare(a.start_time));

  const card = (b: Booking, isPast: boolean) => (
    <div className={isPast ? "card booking past" : "card booking"} key={b.id}>
      <div className="booking-top">
        <span className="booking-room">{rooms[b.room_id]?.name ?? `#${b.room_id}`}</span>
        {!isPast && (
          <button className="link danger" onClick={() => cancel(b.id)}>
            отменить
          </button>
        )}
      </div>
      <div className="booking-when">{fmtDateRange(b.start_time, b.end_time)}</div>
      <div className="booking-title">{b.title}</div>
      {b.comment && <div className="slot-comment">{b.comment}</div>}
      <AmenityChips ids={b.amenities} />
    </div>
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Мои брони</h1>
          <p className="muted">Ваши предстоящие и прошедшие встречи</p>
        </div>
        <Link to="/book" className="btn-link">
          + Новая бронь
        </Link>
      </div>

      {justBooked && <p className="ok banner">Бронь создана ✓</p>}
      {err && <p className="error">{err}</p>}

      {loading ? (
        <p className="muted">Загрузка…</p>
      ) : bookings.length === 0 ? (
        <div className="card empty-state">
          <p>У вас пока нет броней.</p>
          <Link to="/book" className="btn-link">
            Забронировать комнату
          </Link>
        </div>
      ) : (
        <>
          <h3 className="section-title">Предстоящие</h3>
          {upcoming.length ? (
            <div className="booking-grid">{upcoming.map((b) => card(b, false))}</div>
          ) : (
            <p className="muted">нет предстоящих</p>
          )}
          {past.length > 0 && (
            <>
              <h3 className="section-title">Прошедшие</h3>
              <div className="booking-grid">{past.map((b) => card(b, true))}</div>
            </>
          )}
        </>
      )}
    </>
  );
}
