import { useCallback, useEffect, useState } from "react";
import { ApiError, api, type Booking, type Room, type User } from "./api";
import {
  dayBounds,
  fmtDateTime,
  fmtTime,
  isoToLocalInput,
  localInputToISO,
  todayStr,
} from "./time";

interface FormState {
  room_id: string;
  title: string;
  start: string; // datetime-local
  end: string; // datetime-local
}

const emptyForm: FormState = { room_id: "", title: "", start: "", end: "" };

export function Dashboard({ user }: { user: User }) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [day, setDay] = useState(todayStr());
  const [schedule, setSchedule] = useState<Booking[]>([]);
  const [mine, setMine] = useState<Booking[]>([]);
  const [form, setForm] = useState<FormState>(emptyForm);

  const [nlText, setNlText] = useState("");
  const [nlNote, setNlNote] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(
    null,
  );
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.rooms().then(setRooms).catch(() => {});
  }, []);

  const loadSchedule = useCallback(async () => {
    const { from, to } = dayBounds(day);
    const list = await api.bookings({ date_from: from, date_to: to });
    setSchedule(list);
  }, [day]);

  const loadMine = useCallback(async () => {
    setMine(await api.myBookings());
  }, []);

  useEffect(() => {
    loadSchedule();
  }, [loadSchedule]);
  useEffect(() => {
    loadMine();
  }, [loadMine]);

  const roomName = (id: number) =>
    rooms.find((r) => r.id === id)?.name ?? `#${id}`;

  // --- NL: фраза -> черновик -> предзаполнение формы ---
  const parseNL = async () => {
    setNlNote(null);
    setMsg(null);
    setBusy(true);
    try {
      const d = await api.parseNL(nlText);
      setForm({
        room_id: d.room_id ? String(d.room_id) : "",
        title: d.title ?? "",
        start: d.start_time ? isoToLocalInput(d.start_time) : "",
        end: d.end_time ? isoToLocalInput(d.end_time) : "",
      });
      const notes: string[] = [];
      if (d.clarification) notes.push(d.clarification);
      if (d.missing.length) notes.push(`Не хватает: ${d.missing.join(", ")}`);
      setNlNote(
        notes.length
          ? notes.join(" ")
          : "Распознал — проверьте и подтвердите бронь.",
      );
    } catch (err) {
      const text =
        err instanceof ApiError
          ? err.status === 503
            ? "Сервис разбора недоступен. Заполните форму вручную."
            : err.message
          : "Ошибка сети";
      setNlNote(text);
    } finally {
      setBusy(false);
    }
  };

  // --- Создание брони (подтверждение черновика или ручной ввод) ---
  const submitBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    if (!form.room_id || !form.start || !form.end) {
      setMsg({ kind: "err", text: "Заполните комнату, начало и конец." });
      return;
    }
    setBusy(true);
    try {
      await api.createBooking({
        room_id: Number(form.room_id),
        title: form.title || "Без темы",
        start_time: localInputToISO(form.start),
        end_time: localInputToISO(form.end),
      });
      setMsg({ kind: "ok", text: "Бронь создана." });
      setForm(emptyForm);
      setNlText("");
      setNlNote(null);
      await Promise.all([loadSchedule(), loadMine()]);
    } catch (err) {
      const text =
        err instanceof ApiError
          ? err.status === 409
            ? "Комната занята на это время. Выберите другой слот."
            : err.message
          : "Ошибка сети";
      setMsg({ kind: "err", text });
    } finally {
      setBusy(false);
    }
  };

  const cancel = async (id: number) => {
    try {
      await api.cancelBooking(id);
      await Promise.all([loadSchedule(), loadMine()]);
    } catch (err) {
      setMsg({
        kind: "err",
        text: err instanceof ApiError ? err.message : "Ошибка сети",
      });
    }
  };

  return (
    <div className="dashboard">
      {/* ---- Бронь фразой ---- */}
      <section className="card">
        <h3>Забронировать фразой</h3>
        <div className="nl-row">
          <input
            placeholder="забронируй большую переговорку завтра с 14:00 на полтора часа, обсуждение релиза"
            value={nlText}
            onChange={(e) => setNlText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && nlText && parseNL()}
          />
          <button onClick={parseNL} disabled={busy || !nlText}>
            Разобрать
          </button>
        </div>
        {nlNote && <p className="note">{nlNote}</p>}
      </section>

      {/* ---- Форма брони ---- */}
      <section className="card">
        <h3>Новая бронь</h3>
        <form className="booking-form" onSubmit={submitBooking}>
          <label>
            Комната
            <select
              value={form.room_id}
              onChange={(e) => setForm({ ...form, room_id: e.target.value })}
            >
              <option value="">— выбрать —</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} (до {r.capacity})
                </option>
              ))}
            </select>
          </label>
          <label>
            Тема
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label>
            Начало
            <input
              type="datetime-local"
              value={form.start}
              onChange={(e) => setForm({ ...form, start: e.target.value })}
            />
          </label>
          <label>
            Конец
            <input
              type="datetime-local"
              value={form.end}
              onChange={(e) => setForm({ ...form, end: e.target.value })}
            />
          </label>
          <button type="submit" disabled={busy}>
            Забронировать
          </button>
        </form>
        {msg && <p className={msg.kind === "ok" ? "ok" : "error"}>{msg.text}</p>}
      </section>

      {/* ---- Занятость по дню ---- */}
      <section className="card">
        <div className="row-between">
          <h3>Занятость</h3>
          <input
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          />
        </div>
        <div className="rooms-grid">
          {rooms.map((room) => {
            const items = schedule
              .filter((b) => b.room_id === room.id)
              .sort((a, b) => a.start_time.localeCompare(b.start_time));
            return (
              <div className="room-col" key={room.id}>
                <h4>{room.name}</h4>
                {items.length === 0 ? (
                  <p className="muted">свободно весь день</p>
                ) : (
                  items.map((b) => (
                    <div className="slot" key={b.id}>
                      <span className="slot-time">
                        {fmtTime(b.start_time)}–{fmtTime(b.end_time)}
                      </span>
                      <span className="slot-title">{b.title}</span>
                      {(b.user_id === user.id || user.role === "admin") && (
                        <button className="link" onClick={() => cancel(b.id)}>
                          отменить
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ---- Мои брони ---- */}
      <section className="card">
        <h3>Мои брони</h3>
        {mine.length === 0 ? (
          <p className="muted">пока пусто</p>
        ) : (
          <ul className="mine">
            {mine.map((b) => (
              <li key={b.id}>
                <span>
                  {roomName(b.room_id)} · {fmtDateTime(b.start_time)}–
                  {fmtTime(b.end_time)} · {b.title}
                </span>
                <button className="link" onClick={() => cancel(b.id)}>
                  отменить
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
