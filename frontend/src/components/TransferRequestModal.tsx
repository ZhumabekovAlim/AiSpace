import { useState } from "react";
import { ApiError, api, type Booking } from "../api";
import { AmenityPicker } from "./Amenities";
import { isoToLocalInput, localInputToISO } from "../time";

export function TransferRequestModal({
  booking,
  onClose,
  onDone,
}: {
  booking: Booking;
  onClose: () => void;
  onDone: () => void;
}) {
  const [title, setTitle] = useState("");
  const [comment, setComment] = useState("");
  const [amenities, setAmenities] = useState<string[]>([]);
  const [changeTime, setChangeTime] = useState(false);
  const [start, setStart] = useState(isoToLocalInput(booking.start_time));
  const [end, setEnd] = useState(isoToLocalInput(booking.end_time));
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      await api.requestTransfer({
        booking_id: booking.id,
        new_title: title || null,
        new_comment: comment || null,
        new_amenities: amenities.length ? amenities : null,
        new_start_time: changeTime ? localInputToISO(start) : null,
        new_end_time: changeTime ? localInputToISO(end) : null,
      });
      onDone();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Ошибка сети");
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Запросить бронь</h3>
        <p className="muted small">
          «{booking.title}» — владельцу придёт пуш в Telegram. Можно приложить
          свои изменения (применятся при подтверждении).
        </p>
        <form onSubmit={submit} className="transfer-form">
          <label>
            Новая тема <span className="muted">(необязательно)</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="оставить как есть"
            />
          </label>
          <label>
            Комментарий
            <input value={comment} onChange={(e) => setComment(e.target.value)} />
          </label>
          <div>
            <span className="field-label">Допы</span>
            <AmenityPicker selected={amenities} onChange={setAmenities} />
          </div>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={changeTime}
              onChange={(e) => setChangeTime(e.target.checked)}
            />
            изменить время (в той же комнате)
          </label>
          {changeTime && (
            <div className="two-col">
              <label>
                Начало
                <input
                  type="datetime-local"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                />
              </label>
              <label>
                Конец
                <input
                  type="datetime-local"
                  value={end}
                  onChange={(e) => setEnd(e.target.value)}
                />
              </label>
            </div>
          )}
          {msg && <p className="error">{msg}</p>}
          <div className="modal-actions">
            <button type="button" className="ghost" onClick={onClose}>
              Отмена
            </button>
            <button type="submit" disabled={busy}>
              Отправить запрос
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
