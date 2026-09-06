import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError, api, type Room } from "../api";
import { AmenityPicker } from "../components/Amenities";
import { isoToLocalInput, localInputToISO } from "../time";

interface FormState {
  room_id: string;
  title: string;
  comment: string;
  amenities: string[];
  start: string;
  end: string;
}

const empty: FormState = {
  room_id: "",
  title: "",
  comment: "",
  amenities: [],
  start: "",
  end: "",
};

export function BookPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const prefillRoom = (location.state as { roomId?: number } | null)?.roomId;

  const [rooms, setRooms] = useState<Room[]>([]);
  const [form, setForm] = useState<FormState>({
    ...empty,
    room_id: prefillRoom ? String(prefillRoom) : "",
  });
  const [nlText, setNlText] = useState("");
  const [nlNote, setNlNote] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.rooms().then(setRooms).catch(() => {});
  }, []);

  const set = (patch: Partial<FormState>) => setForm((f) => ({ ...f, ...patch }));

  const parseNL = async () => {
    setNlNote(null);
    setMsg(null);
    setBusy(true);
    try {
      const d = await api.parseNL(nlText);
      set({
        room_id: d.room_id ? String(d.room_id) : "",
        title: d.title ?? "",
        start: d.start_time ? isoToLocalInput(d.start_time) : "",
        end: d.end_time ? isoToLocalInput(d.end_time) : "",
      });
      const notes: string[] = [];
      if (d.clarification) notes.push(d.clarification);
      if (d.missing.length) notes.push(`Не хватает: ${d.missing.join(", ")}`);
      setNlNote(notes.length ? notes.join(" ") : "Распознал — проверьте и подтвердите.");
    } catch (err) {
      setNlNote(
        err instanceof ApiError && err.status === 503
          ? "Сервис разбора недоступен. Заполните форму вручную."
          : err instanceof ApiError
            ? err.message
            : "Ошибка сети",
      );
    } finally {
      setBusy(false);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    if (!form.room_id || !form.start || !form.end) {
      setMsg({ ok: false, text: "Заполните комнату, начало и конец." });
      return;
    }
    setBusy(true);
    try {
      await api.createBooking({
        room_id: Number(form.room_id),
        title: form.title || "Без темы",
        comment: form.comment || null,
        amenities: form.amenities,
        start_time: localInputToISO(form.start),
        end_time: localInputToISO(form.end),
      });
      navigate("/my", { state: { justBooked: true } });
    } catch (err) {
      setMsg({
        ok: false,
        text:
          err instanceof ApiError && err.status === 409
            ? "Комната занята на это время. Выберите другой слот."
            : err instanceof ApiError
              ? err.message
              : "Ошибка сети",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Новая бронь</h1>
          <p className="muted">Заполните форму или опишите бронь фразой</p>
        </div>
      </div>

      <section className="card nl-card">
        <label className="nl-label">✨ Бронь одной фразой</label>
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

      <section className="card">
        <form className="booking-form" onSubmit={submit}>
          <label>
            Комната
            <select
              value={form.room_id}
              onChange={(e) => set({ room_id: e.target.value })}
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
            Тема встречи
            <input
              value={form.title}
              onChange={(e) => set({ title: e.target.value })}
              placeholder="Например: обсуждение релиза"
            />
          </label>
          <label>
            Начало
            <input
              type="datetime-local"
              value={form.start}
              onChange={(e) => set({ start: e.target.value })}
            />
          </label>
          <label>
            Конец
            <input
              type="datetime-local"
              value={form.end}
              onChange={(e) => set({ end: e.target.value })}
            />
          </label>
          <label className="full">
            Комментарий
            <textarea
              value={form.comment}
              onChange={(e) => set({ comment: e.target.value })}
              placeholder="Пожелания: нужен доступ к экрану, тихая комната…"
              rows={2}
            />
          </label>
          <div className="full">
            <span className="field-label">Допы</span>
            <AmenityPicker
              selected={form.amenities}
              onChange={(amenities) => set({ amenities })}
            />
          </div>
          {msg && <p className={msg.ok ? "ok full" : "error full"}>{msg.text}</p>}
          <button type="submit" className="full primary-lg" disabled={busy}>
            Забронировать
          </button>
        </form>
      </section>
    </>
  );
}
