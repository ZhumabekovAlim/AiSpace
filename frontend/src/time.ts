// Хелперы времени. Бэкенд принимает/отдаёт ISO 8601 с таймзоной.
// Инпуты datetime-local работают в локальном времени пользователя.

export function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

// Границы выбранного дня (локальные) в ISO — для запроса занятости.
export function dayBounds(day: string): { from: string; to: string } {
  const from = new Date(`${day}T00:00`);
  const to = new Date(from);
  to.setDate(to.getDate() + 1);
  return { from: from.toISOString(), to: to.toISOString() };
}

// value из <input type="datetime-local"> ("2026-09-07T14:00") -> ISO UTC.
export function localInputToISO(v: string): string {
  return new Date(v).toISOString();
}

// ISO с таймзоной -> строка для datetime-local в локальном времени.
export function isoToLocalInput(iso: string): string {
  const d = new Date(iso);
  const off = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - off).toISOString().slice(0, 16);
}

// Человекочитаемое время брони.
export function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Ключ локального дня "YYYY-MM-DD" для группировки.
export function dayKey(iso: string): string {
  const d = new Date(iso);
  const off = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - off).toISOString().slice(0, 10);
}

// "12 сентября, пятница" — заголовок группы истории.
export function fmtDayLong(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    weekday: "long",
  });
}

// "12 сент, 14:00–15:30" — дата один раз, оба конца времени.
export function fmtDateRange(startIso: string, endIso: string): string {
  const date = new Date(startIso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
  });
  return `${date}, ${fmtTime(startIso)}–${fmtTime(endIso)}`;
}
