import { useCallback, useEffect, useState } from "react";
import { ApiError, api, type Transfer, type TransferStatus } from "../api";
import { AmenityChips } from "../components/Amenities";
import { fmtDateRange } from "../time";

const STATUS_LABEL: Record<TransferStatus, string> = {
  pending: "ожидает",
  accepted: "принята",
  rejected: "отклонена",
  cancelled: "отменена",
};

export function TransfersPage() {
  const [incoming, setIncoming] = useState<Transfer[]>([]);
  const [outgoing, setOutgoing] = useState<Transfer[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const d = await api.transfers();
    setIncoming(d.incoming);
    setOutgoing(d.outgoing);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (id: number, action: "accept" | "reject" | "cancel") => {
    setErr(null);
    try {
      await api.resolveTransfer(id, action);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Ошибка сети");
    }
  };

  const changes = (t: Transfer) => {
    const parts: string[] = [];
    if (t.new_title) parts.push(`тема: «${t.new_title}»`);
    if (t.new_comment) parts.push(`комментарий: «${t.new_comment}»`);
    if (t.new_start_time && t.new_end_time)
      parts.push(`время: ${fmtDateRange(t.new_start_time, t.new_end_time)}`);
    return parts;
  };

  const badge = (s: TransferStatus) => (
    <span className={`status ${s === "accepted" ? "ok" : s === "pending" ? "" : "off"}`}>
      {STATUS_LABEL[s]}
    </span>
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Передачи броней</h1>
          <p className="muted">Запросы на ваши брони и ваши запросы к другим</p>
        </div>
      </div>

      {err && <p className="error">{err}</p>}
      {loading && <p className="muted">Загрузка…</p>}

      <h3 className="section-title">Входящие (просят вашу бронь)</h3>
      {incoming.length === 0 ? (
        <p className="muted">нет запросов</p>
      ) : (
        <div className="booking-grid">
          {incoming.map((t) => (
            <div className="card booking" key={t.id}>
              <div className="booking-top">
                <span className="booking-room">{t.room_name}</span>
                {badge(t.status)}
              </div>
              <div className="booking-when">
                {fmtDateRange(t.booking.start_time, t.booking.end_time)}
              </div>
              <div className="booking-title">{t.booking.title}</div>
              <p className="muted small">Запросил: {t.to_user.full_name}</p>
              {changes(t).length > 0 && (
                <div className="slot-comment">Изменит → {changes(t).join("; ")}</div>
              )}
              {t.new_amenities && <AmenityChips ids={t.new_amenities} />}
              {t.status === "pending" && (
                <div className="row-actions" style={{ marginTop: 10 }}>
                  <button className="link" onClick={() => act(t.id, "accept")}>
                    ✅ передать
                  </button>
                  <button className="link danger" onClick={() => act(t.id, "reject")}>
                    ❌ отклонить
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <h3 className="section-title">Исходящие (вы просите)</h3>
      {outgoing.length === 0 ? (
        <p className="muted">нет запросов</p>
      ) : (
        <div className="booking-grid">
          {outgoing.map((t) => (
            <div className="card booking" key={t.id}>
              <div className="booking-top">
                <span className="booking-room">{t.room_name}</span>
                {badge(t.status)}
              </div>
              <div className="booking-when">
                {fmtDateRange(t.booking.start_time, t.booking.end_time)}
              </div>
              <div className="booking-title">{t.booking.title}</div>
              <p className="muted small">Владелец: {t.from_user.full_name}</p>
              {t.status === "pending" && (
                <div className="row-actions" style={{ marginTop: 10 }}>
                  <button className="link danger" onClick={() => act(t.id, "cancel")}>
                    отменить запрос
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
