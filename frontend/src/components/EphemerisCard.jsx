const TYPE_LABEL = {
  Nacimiento: { label: "Nacimiento", color: "text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-700" },
  Fallecimiento: { label: "Fallecimiento", color: "text-rose-700 dark:text-rose-400 border-rose-300 dark:border-rose-700" },
  Evento: { label: "Evento", color: "text-gold-dark dark:text-gold-light border-gold dark:border-gold-dark" },
};

export default function EphemerisCard({ ephemeris }) {
  const { label, color } = TYPE_LABEL[ephemeris.type] || TYPE_LABEL.Evento;
  const image = ephemeris.images?.[0];
  const url = ephemeris.urls?.[0];

  return (
    <article className="group flex gap-4 py-6 border-b border-parchment-dark dark:border-ink-light last:border-0">
      {image && (
        <a href={url} target="_blank" rel="noopener noreferrer" className="shrink-0">
          <img
            src={image}
            alt={ephemeris.title}
            className="w-20 h-20 object-cover rounded grayscale group-hover:grayscale-0 transition-all duration-500"
          />
        </a>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`font-mono text-xs border px-1.5 py-0.5 rounded ${color}`}>
            {label}
          </span>
          <span className="font-mono text-xs text-muted">{ephemeris.date}</span>
        </div>
        <h2 className="font-display text-base font-semibold leading-snug mb-1 text-ink dark:text-parchment">
          {ephemeris.title}
        </h2>
        <p className="text-sm text-muted leading-relaxed line-clamp-3">
          {ephemeris.description}
        </p>
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block mt-2 text-xs text-gold hover:text-gold-dark dark:hover:text-gold-light transition-colors"
          >
            Ver en Wikipedia →
          </a>
        )}
      </div>
    </article>
  );
}
