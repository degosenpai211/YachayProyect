import { Link } from "react-router-dom";
import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import {
  fetchExperiments,
  fetchStats,
  fetchStudent,
  fetchStudents,
  fetchWeaknesses,
  resolveWeakness,
  updateExperiment,
  API_URL,
} from "../api.js";
import { TOPIC_LABELS } from "../data/mock.js";
import StatCard from "../components/StatCard.jsx";
import StudentDetail from "../components/StudentDetail.jsx";

function downloadCsv(filename, rows) {
  const escape = (v) => {
    const s = String(v ?? "");
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const csv = rows.map((r) => r.map(escape).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [students, setStudents] = useState([]);
  const [weaknesses, setWeaknesses] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [course, setCourse] = useState("");
  const [search, setSearch] = useState("");
  const [, startTransition] = useTransition();

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const courseArg = course || undefined;
      const [s, st, w, e] = await Promise.all([
        fetchStats(),
        fetchStudents(courseArg),
        fetchWeaknesses(courseArg),
        fetchExperiments(courseArg),
      ]);
      startTransition(() => {
        setStats(s);
        setStudents(st);
        setWeaknesses(w);
        setExperiments(e);
      });
    } catch (err) {
      setStats({ students: 0, messages: 0, active_weaknesses: 0, experiments: 0, topics: [] });
      setStudents([]);
      setWeaknesses([]);
      setExperiments([]);
      setError(`No se pudo conectar al backend (${API_URL}). Revisa Railway / VITE_API_URL.`);
    } finally {
      setLoading(false);
    }
  }, [course]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (cancelled) return;
      await load();
    })();
    const id = setInterval(() => {
      if (!cancelled) load();
    }, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [load]);

  const topicLabelMap = useMemo(() => {
    const map = { ...TOPIC_LABELS };
    for (const t of stats?.topics || []) {
      map[t.topic] = t.topic_label;
    }
    return map;
  }, [stats]);
  const topicLabel = (id) => topicLabelMap[id] || id;

  const courses = useMemo(() => {
    const set = new Set(students.map((s) => s.course).filter(Boolean));
    return Array.from(set).sort();
  }, [students]);

  const q = search.trim().toLowerCase();
  const filteredStudents = useMemo(() => {
    if (!q) return students;
    return students.filter(
      (s) =>
        s.code.toLowerCase().includes(q) ||
        (s.display_name || "").toLowerCase().includes(q) ||
        (s.course || "").toLowerCase().includes(q),
    );
  }, [students, q]);

  const filteredWeaknesses = useMemo(() => {
    if (!q) return weaknesses;
    return weaknesses.filter(
      (w) =>
        w.student_code.toLowerCase().includes(q) ||
        (w.student_name || "").toLowerCase().includes(q) ||
        topicLabel(w.topic).toLowerCase().includes(q),
    );
  }, [weaknesses, q, topicLabelMap]);

  const filteredExperiments = useMemo(() => {
    if (!q) return experiments;
    return experiments.filter(
      (e) =>
        e.student_code.toLowerCase().includes(q) ||
        (e.student_name || "").toLowerCase().includes(q) ||
        (e.title || "").toLowerCase().includes(q) ||
        topicLabel(e.topic).toLowerCase().includes(q),
    );
  }, [experiments, q, topicLabelMap]);

  async function openStudent(student) {
    setSelected(student);
    setDetail(null);
    setDetailError("");
    setDetailLoading(true);
    try {
      const full = await fetchStudent(student.code);
      setDetail(full);
    } catch (err) {
      setDetailError("No se pudo cargar el detalle del alumno.");
    } finally {
      setDetailLoading(false);
    }
  }

  function closeStudent() {
    setSelected(null);
    setDetail(null);
    setDetailError("");
  }

  async function onResolveWeakness(id) {
    try {
      await resolveWeakness(id);
      setWeaknesses((prev) => prev.filter((w) => w.id !== id));
      load();
    } catch {
      setError("No se pudo marcar la debilidad como resuelta.");
    }
  }

  async function onExperimentStatus(id, status) {
    try {
      const updated = await updateExperiment(id, { status });
      setExperiments((prev) => prev.map((e) => (e.id === id ? { ...e, ...updated } : e)));
    } catch {
      setError("No se pudo actualizar el experimento.");
    }
  }

  function exportStudentsCsv() {
    const rows = [
      ["codigo", "nombre", "curso", "mensajes", "debilidades"],
      ...filteredStudents.map((s) => [
        s.code,
        s.display_name,
        s.course,
        s.message_count,
        s.weakness_count,
      ]),
    ];
    downloadCsv("yachay-estudiantes.csv", rows);
  }

  function exportWeaknessesCsv() {
    const rows = [
      ["alumno", "codigo", "tema", "hits"],
      ...filteredWeaknesses.map((w) => [
        w.student_name,
        w.student_code,
        topicLabel(w.topic),
        w.hit_count,
      ]),
    ];
    downloadCsv("yachay-debilidades.csv", rows);
  }

  return (
    <div className="min-h-screen px-4 py-6 md:px-10 md:py-8">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link to="/" className="brand text-xl font-bold text-[var(--leaf-deep)]">
            Yachay
          </Link>
          <h1 className="mt-1 text-2xl font-semibold md:text-3xl">Dashboard docente</h1>
          <p className="mt-1 text-sm text-[var(--ink)]/60">
            Alumnos individuales + temas débiles agregados
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={exportStudentsCsv}
            className="rounded-lg border border-[var(--line)] bg-white/70 px-4 py-2 text-sm font-medium"
          >
            Exportar CSV
          </button>
          <button
            type="button"
            onClick={() => load()}
            className="rounded-lg border border-[var(--line)] bg-white/70 px-4 py-2 text-sm font-medium"
          >
            Actualizar
          </button>
        </div>
      </header>

      <div className="mb-6 flex flex-wrap gap-3">
        <label className="flex flex-col text-xs text-[var(--ink)]/55">
          Curso
          <select
            value={course}
            onChange={(e) => setCourse(e.target.value)}
            className="mt-1 rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm text-[var(--ink)]"
          >
            <option value="">Todos</option>
            {courses.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex min-w-[220px] flex-1 flex-col text-xs text-[var(--ink)]/55">
          Buscar
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Código, nombre o tema…"
            className="mt-1 rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm text-[var(--ink)]"
          />
        </label>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {error}
        </div>
      )}

      {loading && !stats ? (
        <p className="text-[var(--ink)]/50">Cargando métricas…</p>
      ) : (
        <>
          <section className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
            <StatCard label="Estudiantes" value={stats?.students ?? 0} />
            <StatCard label="Mensajes" value={stats?.messages ?? 0} />
            <StatCard label="Debilidades" value={stats?.active_weaknesses ?? 0} accent />
            <StatCard label="Experimentos" value={stats?.experiments ?? 0} />
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-[var(--line)] bg-[var(--card)] p-5 backdrop-blur">
              <h2 className="text-lg font-semibold">Temas con más dificultad</h2>
              <p className="mb-4 text-sm text-[var(--ink)]/55">Vista agregada del curso</p>
              {(stats?.topics || []).length === 0 ? (
                <p className="text-sm text-[var(--ink)]/45">Aún no hay debilidades detectadas.</p>
              ) : (
                <ul className="space-y-3">
                  {stats.topics.map((t) => (
                    <li key={t.topic} className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-medium">{t.topic_label}</p>
                        <p className="text-xs text-[var(--ink)]/50">
                          {t.student_count} alumno(s) · {t.total_hits} hits
                        </p>
                      </div>
                      <div className="h-2 w-28 overflow-hidden rounded-full bg-[var(--fog)]">
                        <div
                          className="h-full rounded-full bg-[var(--clay)]"
                          style={{ width: `${Math.min(100, t.total_hits * 25)}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-2xl border border-[var(--line)] bg-[var(--card)] p-5 backdrop-blur">
              <div className="mb-4 flex items-center justify-between gap-2">
                <div>
                  <h2 className="text-lg font-semibold">Debilidades por alumno</h2>
                  <p className="text-sm text-[var(--ink)]/55">Detalle individual</p>
                </div>
                <button
                  type="button"
                  onClick={exportWeaknessesCsv}
                  className="text-xs font-medium text-[var(--leaf-deep)] underline"
                >
                  CSV
                </button>
              </div>
              {filteredWeaknesses.length === 0 ? (
                <p className="text-sm text-[var(--ink)]/45">Sin registros activos.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-[var(--ink)]/50">
                      <tr>
                        <th className="pb-2 font-medium">Alumno</th>
                        <th className="pb-2 font-medium">Tema</th>
                        <th className="pb-2 font-medium">Hits</th>
                        <th className="pb-2 font-medium">Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredWeaknesses.map((w) => (
                        <tr key={w.id} className="border-t border-[var(--line)]">
                          <td className="py-2.5">
                            <span className="font-medium">{w.student_name}</span>
                            <span className="ml-2 text-xs text-[var(--ink)]/45">{w.student_code}</span>
                          </td>
                          <td className="py-2.5">{topicLabel(w.topic)}</td>
                          <td className="py-2.5 font-semibold text-[var(--clay)]">{w.hit_count}</td>
                          <td className="py-2.5">
                            <button
                              type="button"
                              onClick={() => onResolveWeakness(w.id)}
                              className="rounded-md border border-[var(--line)] px-2 py-1 text-xs font-medium hover:bg-white"
                            >
                              Resuelta
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>

          <section className="mt-6 rounded-2xl border border-[var(--line)] bg-[var(--card)] p-5 backdrop-blur">
            <h2 className="text-lg font-semibold">Estudiantes</h2>
            <p className="mb-4 text-sm text-[var(--ink)]/55">Haz clic para ver actividad</p>
            {filteredStudents.length === 0 ? (
              <p className="text-sm text-[var(--ink)]/45">
                Sin alumnos aún. Que escriban al bot con su código (ej. UEBOL-3A-12).
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-[var(--ink)]/50">
                    <tr>
                      <th className="pb-2 font-medium">Código</th>
                      <th className="pb-2 font-medium">Nombre</th>
                      <th className="pb-2 font-medium">Curso</th>
                      <th className="pb-2 font-medium">Msgs</th>
                      <th className="pb-2 font-medium">Debilidades</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStudents.map((s) => (
                      <tr
                        key={s.id}
                        className="cursor-pointer border-t border-[var(--line)] hover:bg-white/50"
                        onClick={() => openStudent(s)}
                      >
                        <td className="py-2.5 font-mono text-xs">{s.code}</td>
                        <td className="py-2.5 font-medium">{s.display_name}</td>
                        <td className="py-2.5">{s.course}</td>
                        <td className="py-2.5">{s.message_count}</td>
                        <td className="py-2.5">
                          <span
                            className={
                              s.weakness_count > 0
                                ? "font-semibold text-[var(--clay)]"
                                : "text-[var(--ink)]/40"
                            }
                          >
                            {s.weakness_count}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="mt-6 rounded-2xl border border-[var(--line)] bg-[var(--card)] p-5 backdrop-blur">
            <h2 className="text-lg font-semibold">Experimentos</h2>
            {filteredExperiments.length === 0 ? (
              <p className="mt-2 text-sm text-[var(--ink)]/45">Todavía no se armó ninguno.</p>
            ) : (
              <ul className="mt-4 space-y-4">
                {filteredExperiments.map((e) => (
                  <li key={e.id} className="border-t border-[var(--line)] pt-4 first:border-0 first:pt-0">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold">{e.title}</p>
                        <p className="text-xs text-[var(--ink)]/50">
                          {e.student_name} · {e.student_code} · {topicLabel(e.topic)}
                        </p>
                      </div>
                      <span
                        className={
                          e.status === "done"
                            ? "rounded-full bg-[var(--leaf)]/15 px-2.5 py-1 text-xs font-semibold text-[var(--leaf-deep)]"
                            : "rounded-full bg-[var(--sun)]/20 px-2.5 py-1 text-xs font-semibold text-[var(--ink)]"
                        }
                      >
                        {e.status === "done" ? "Hecho" : "Pendiente"}
                      </span>
                    </div>
                    <p className="mt-2 text-sm">
                      <span className="font-medium">Materiales:</span> {e.materials}
                    </p>
                    <p className="mt-1 whitespace-pre-line text-sm text-[var(--ink)]/80">{e.steps}</p>
                    {e.feedback ? (
                      <p className="mt-2 text-sm italic text-[var(--ink)]/70">
                        Feedback alumno: {e.feedback}
                      </p>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {e.status !== "done" ? (
                        <button
                          type="button"
                          onClick={() => onExperimentStatus(e.id, "done")}
                          className="rounded-md border border-[var(--line)] px-3 py-1.5 text-xs font-medium hover:bg-white"
                        >
                          Marcar hecho
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => onExperimentStatus(e.id, "pending")}
                          className="rounded-md border border-[var(--line)] px-3 py-1.5 text-xs font-medium hover:bg-white"
                        >
                          Volver a pendiente
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {selected && (
        <StudentDetail
          student={selected}
          detail={detail}
          loading={detailLoading}
          error={detailError}
          topicLabel={topicLabel}
          onClose={closeStudent}
        />
      )}
    </div>
  );
}
