import { useApp } from "../context";

/** Отображение выбранных допов чипами с иконками. */
export function AmenityChips({ ids }: { ids: string[] }) {
  const { amenityMap } = useApp();
  if (!ids.length) return null;
  return (
    <span className="chips">
      {ids.map((id) => {
        const a = amenityMap[id];
        return (
          <span className="chip" key={id} title={a?.label ?? id}>
            {a ? `${a.icon} ${a.label}` : id}
          </span>
        );
      })}
    </span>
  );
}

/** Выбор допов галочками (toggle). */
export function AmenityPicker({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const { amenities } = useApp();
  const toggle = (id: string) =>
    onChange(
      selected.includes(id)
        ? selected.filter((x) => x !== id)
        : [...selected, id],
    );

  return (
    <div className="amenity-picker">
      {amenities.map((a) => {
        const on = selected.includes(a.id);
        return (
          <button
            type="button"
            key={a.id}
            className={on ? "amenity on" : "amenity"}
            onClick={() => toggle(a.id)}
          >
            <span className="amenity-icon">{a.icon}</span>
            {a.label}
          </button>
        );
      })}
    </div>
  );
}
