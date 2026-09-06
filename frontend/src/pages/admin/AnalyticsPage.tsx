import { useEffect, useState } from "react";
import { api, type Analytics } from "../../api";
import { useApp } from "../../context";
import { todayStr } from "../../time";

function StatTile({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="stat-tile">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

/** Горизонтальные бары: label + значение, ширина пропорциональна max. */
function BarList({
  items,
}: {
  items: { label: string; count: number }[];
}) {
  const max = Math.max(1, ...items.map((i) => i.count));
  if (!items.length) return <p className="muted">нет данных</p>;
  return (
    <div className="bar-list">
      {items.map((i) => (
        <div className="bar-row" key={i.label}>
          <span className="bar-label">{i.label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(i.count / max) * 100}%` }} />
          </div>
          <span className="bar-count">{i.count}</span>
        </div>
      ))}
    </div>
  );
}

export function AnalyticsPage() {
  const { amenityMap } = useApp();
  const [data, setData] = useState<Analytics | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .analytics()
      .then(setData)
      .catch((e) => setErr(e.message ?? "Ошибка"));
  }, []);

  if (err) return <p className="error">{err}</p>;
  if (!data) return <p className="muted">Загрузка…</p>;

  const today = todayStr();
  const maxDay = Math.max(1, ...data.per_day.map((d) => d.count));

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Аналитика</h1>
          <p className="muted">Загрузка переговорных и активность</p>
        </div>
      </div>

      <div className="stat-row">
        <StatTile value={data.total_bookings} label="Всего броней" />
        <StatTile value={data.upcoming_bookings} label="Предстоящих" />
        <StatTile value={data.active_rooms} label="Активных комнат" />
        <StatTile value={data.total_users} label="Пользователей" />
        <StatTile value={`${data.total_hours} ч`} label="Часов забронировано" />
      </div>

      <section className="card">
        <h3>Активность по дням (±неделя)</h3>
        <div className="day-chart">
          {data.per_day.map((d) => (
            <div className="day-col" key={d.date} title={`${d.date}: ${d.count}`}>
              <div className="day-bar-wrap">
                <div
                  className={d.date === today ? "day-bar today" : "day-bar"}
                  style={{ height: `${(d.count / maxDay) * 100}%` }}
                >
                  {d.count > 0 && <span className="day-bar-num">{d.count}</span>}
                </div>
              </div>
              <span className="day-tick">{d.date.slice(8)}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="analytics-grid">
        <section className="card">
          <h3>Брони по комнатам</h3>
          <BarList items={data.per_room} />
        </section>

        <section className="card">
          <h3>Активные пользователи</h3>
          <BarList items={data.top_users} />
        </section>

        <section className="card">
          <h3>Популярные допы</h3>
          <BarList
            items={data.amenities.map((a) => {
              const meta = amenityMap[a.label];
              return {
                label: meta ? `${meta.icon} ${meta.label}` : a.label,
                count: a.count,
              };
            })}
          />
        </section>
      </div>
    </>
  );
}
