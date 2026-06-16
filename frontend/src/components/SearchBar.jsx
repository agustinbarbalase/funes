import { useState } from "react";

const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export default function SearchBar({ onDateSearch, onQuerySearch, loading }) {
  const today = new Date();
  const [mode, setMode] = useState("date");
  const [day, setDay] = useState(today.getDate());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [query, setQuery] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (mode === "date") onDateSearch(month, day);
    else if (query.trim()) onQuerySearch(query.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Mode toggle */}
      <div className="flex gap-1 p-1 bg-parchment-dark dark:bg-ink-light rounded-lg w-fit">
        {["date", "query"].map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`px-4 py-1.5 text-sm rounded-md transition-all ${
              mode === m
                ? "bg-ink dark:bg-parchment text-parchment dark:text-ink font-medium shadow-sm"
                : "text-muted hover:text-ink dark:hover:text-parchment"
            }`}
          >
            {m === "date" ? "Por fecha" : "Por consulta"}
          </button>
        ))}
      </div>

      {mode === "date" ? (
        <div className="flex gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted font-mono uppercase tracking-wider">Día</label>
            <input
              type="number"
              min={1}
              max={31}
              value={day}
              onChange={(e) => setDay(Number(e.target.value))}
              className="w-20 px-3 py-2 bg-white dark:bg-ink-light border border-parchment-dark dark:border-ink-light rounded-lg text-ink dark:text-parchment focus:outline-none focus:ring-2 focus:ring-gold"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted font-mono uppercase tracking-wider">Mes</label>
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="px-3 py-2 bg-white dark:bg-ink-light border border-parchment-dark dark:border-ink-light rounded-lg text-ink dark:text-parchment focus:outline-none focus:ring-2 focus:ring-gold"
            >
              {MONTHS.map((m, i) => (
                <option key={i + 1} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
          <SubmitButton loading={loading} />
        </div>
      ) : (
        <div className="flex gap-3 items-end">
          <div className="flex flex-col gap-1 flex-1">
            <label className="text-xs text-muted font-mono uppercase tracking-wider">Consulta</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="ej. batallas navales del siglo XIX"
              className="px-3 py-2 bg-white dark:bg-ink-light border border-parchment-dark dark:border-ink-light rounded-lg text-ink dark:text-parchment placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-gold"
            />
          </div>
          <SubmitButton loading={loading} />
        </div>
      )}
    </form>
  );
}

function SubmitButton({ loading }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="px-5 py-2 bg-ink dark:bg-parchment text-parchment dark:text-ink rounded-lg font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
    >
      {loading ? "Buscando…" : "Buscar"}
    </button>
  );
}