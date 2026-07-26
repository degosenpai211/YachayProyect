export default function StudentDetail({ student, detail, loading, error, topicLabel, onClose }) {
  const messages = detail?.messages || [];
  const weaknesses = detail?.weaknesses || [];
  const experiments = detail?.experiments || [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-8"
      onClick={onClose}
    >
      <div
        className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-[var(--line)] bg-[var(--card)] p-6 shadow-2xl backdrop-blur"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">{student.display_name}</h2>
            <p className="text-xs text-[var(--ink)]/50">
              {student.code} · {student.course}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-[var(--line)] bg-white/70 px-3 py-1.5 text-sm font-medium"
          >
            Cerrar
          </button>
        </div>

        {loading && <p className="text-sm text-[var(--ink)]/50">Cargando actividad…</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}

        {!loading && !error && (
          <>
            {weaknesses.length > 0 && (
              <div className="mb-5">
                <h3 className="mb-2 text-sm font-semibold text-[var(--clay)]">Debilidades activas</h3>
                <ul className="flex flex-wrap gap-2">
                  {weaknesses.map((w) => (
                    <li
                      key={w.id}
                      className="rounded-full bg-[var(--clay)]/10 px-3 py-1 text-xs font-medium text-[var(--clay)]"
                    >
                      {topicLabel(w.topic)} · {w.hit_count} hits
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {experiments.length > 0 && (
              <div className="mb-5">
                <h3 className="mb-2 text-sm font-semibold">Mini-experimentos</h3>
                <ul className="space-y-3">
                  {experiments.map((e) => (
                    <li key={e.id} className="rounded-xl border border-[var(--line)] p-3 text-sm">
                      <p className="font-medium">{e.title}</p>
                      <p className="text-xs text-[var(--ink)]/50">{topicLabel(e.topic)}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h3 className="mb-2 text-sm font-semibold">Conversación</h3>
              {messages.length === 0 ? (
                <p className="text-sm text-[var(--ink)]/45">Todavía no hay mensajes.</p>
              ) : (
                <ul className="space-y-2">
                  {messages.map((m) => (
                    <li
                      key={m.id}
                      className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                        m.role === "student"
                          ? "ml-0 bg-white/70"
                          : "ml-auto bg-[var(--leaf)]/10 text-right"
                      }`}
                    >
                      <p className="whitespace-pre-line">{m.content}</p>
                      {m.topic && (
                        <p className="mt-1 text-[10px] uppercase tracking-wide text-[var(--ink)]/40">
                          {topicLabel(m.topic)}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
