import { useState } from "react";
import { useTheme } from "./hooks/useTheme";
import { getEphemeris, searchEphemeris } from "./lib/api";
import SearchBar from "./components/SearchBar";
import EphemerisCard from "./components/EphemerisCard";

export default function App() {
  const [dark, toggleTheme] = useTheme();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  async function handleDateSearch(month, day) {
    setLoading(true);
    setError(null);
    try {
      const data = await getEphemeris(month, day);
      setResults(Array.isArray(data) ? data : data.ephemerides ?? []);
      setSearched(true);
    } catch (e) {
      setError("No se pudo obtener las efemérides. Intentá de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  async function handleQuerySearch(query) {
    setLoading(true);
    setError(null);
    try {
      const data = await searchEphemeris(query);
      setResults(Array.isArray(data) ? data : data.ephemerides ?? []);
      setSearched(true);
    } catch (e) {
      setError("No se pudo realizar la búsqueda. Intentá de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-parchment dark:bg-ink transition-colors duration-300">
      <div className="max-w-2xl mx-auto px-4 py-12">

        {/* Header */}
        <header className="flex items-start justify-between mb-12">
          <div>
            <h1 className="font-display text-4xl font-bold text-ink dark:text-parchment leading-none">
              Funes
            </h1>
            <p className="mt-1 text-sm text-muted font-mono">Efemérides Históricas</p>
          </div>
          <button
            onClick={toggleTheme}
            aria-label="Cambiar tema"
            className="mt-1 w-9 h-9 flex items-center justify-center rounded-full border border-parchment-dark dark:border-ink-light text-muted hover:text-ink dark:hover:text-parchment hover:border-gold transition-all"
          >
            {dark ? "☀" : "☾"}
          </button>
        </header>

        {/* Quote */}
        <blockquote className="mb-10 pl-4 border-l-2 border-gold">
          <p className="font-display italic text-sm text-muted leading-relaxed">
            "Pensar es olvidar diferencias, es generalizar, abstraer. En el abarrotado
            mundo de Funes no había sino detalles, casi inmediatos."
          </p>
          <cite className="block mt-1 text-xs text-muted font-mono not-italic">
            — Jorge Luis Borges, <em>Funes el memorioso</em>
          </cite>
        </blockquote>

        {/* Search */}
        <SearchBar
          onDateSearch={handleDateSearch}
          onQuerySearch={handleQuerySearch}
          loading={loading}
        />

        {/* Results */}
        <div className="mt-10">
          {loading && (
            <div className="space-y-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex gap-4 py-6 border-b border-parchment-dark dark:border-ink-light animate-pulse">
                  <div className="w-20 h-20 bg-parchment-dark dark:bg-ink-light rounded shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-24 bg-parchment-dark dark:bg-ink-light rounded" />
                    <div className="h-4 w-3/4 bg-parchment-dark dark:bg-ink-light rounded" />
                    <div className="h-3 w-full bg-parchment-dark dark:bg-ink-light rounded" />
                    <div className="h-3 w-2/3 bg-parchment-dark dark:bg-ink-light rounded" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && (
            <p className="text-sm text-rose-600 dark:text-rose-400 font-mono">{error}</p>
          )}

          {!loading && searched && results.length === 0 && (
            <p className="text-sm text-muted font-mono">
              Sin resultados. Probá con otra fecha o consulta.
            </p>
          )}

          {!loading && results.length > 0 && (
            <div>
              <p className="text-xs text-muted font-mono mb-4">
                {results.length} {results.length === 1 ? "efeméride" : "efemérides"}
              </p>
              {results.map((e, i) => (
                <EphemerisCard key={e.source_id ?? i} ephemeris={e} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
