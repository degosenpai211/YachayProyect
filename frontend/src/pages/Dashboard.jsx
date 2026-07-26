import { Link } from "react-router-dom";
import { useEffect, useMemo, useState, useTransition } from "react";
import {
  fetchExperiments,
  fetchStats,
  fetchStudent,
  fetchStudents,
  fetchWeaknesses,
  API_URL,
} from "../api.js";
import {
  MOCK_EXPERIMENTS,
  MOCK_STATS,
  MOCK_STUDENTS,
  MOCK_WEAKNESSES,
  TOPIC_LABELS,
} from "../data/mock.js";
import StatCard from "../components/StatCard.jsx";
import StudentDetail from "../components/StudentDetail.jsx";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [students, setStudents] = useState([]);
  const [weaknesses, setWeaknesses] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [usingMock, setUsingMock] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const [s, st, w, e] = await Promise.all([
          fetchStats(),
          fetchStudents(),
          fetchWeaknesses(),
          fetchExperiments(),
        ]);
        if (cancelled) return;
        startTransition(() => {
          setStats(s);
          setStudents(st);
          setWeaknesses(w);
          setExperiments(e);
          setUsingMock(false);
        });
      } catch (err) {
        if (cancelled) return;
        setStats(MOCK_STATS);
        setStudents(MOCK_STUDENTS);
        setWeaknesses(MOCK_WEAKNESSES);
        setExperiments(MOCK_EXPERIMENTS);
        setUsingMock(true);
        setError(`Backend no disponible (${API_URL}). Mostrando datos mock.`);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const id = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  // El backend (app/topics.py) es la fuente de verdad de los labels; los de
  // mock.js son solo fallback offline. Cuando hay datos reales, los del API
  // tienen prioridad.
  const topicLabelMap = useMemo(() => {
    const map = { ...TOPIC_LABELS };
    for (const t of stats?.topics || []) {
      map[t.topic] = t.topic_label;
    }
    return map;
  }, [stats]);
  const topicLabel = (id) => topicLabelMap[id] || id;

  async function openStudent(student) {
    setSelected(student);
    setDetail(null);
    setDetailError("");

    if (usingMock) {
      setDetail({
        ...student,
        messages: [],
        weaknesses: MOCK_WEAKNESSES.filter((w) => w.student_code === student.code),
        experiments: MOCK_EXPERIMENTS.filter((e) => e.student_code === student.code),
      });
      return;
    }

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
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="rounded-lg border border-[var(--line)] bg-white/70 px-4 py-2 text-sm font-medium"
        >
          Actualizar
        </button>
      </header>

      {usingMock && (
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
              <h2 className="text-lg font-semibold">Debilidades por alumno</h2>
              <p className="mb-4 text-sm text-[var(--ink)]/55">Detalle individual</p>
              {weaknesses.length === 0 ? (
                <p className="text-sm text-[var(--ink)]/45">Sin registros activos.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-[var(--ink)]/50">
                      <tr>
                        <th className="pb-2 font-medium">Alumno</th>
                        <th className="pb-2 font-medium">Tema</th>
                        <th className="pb-2 font-medium">Hits</th>
                      </tr>
                    </thead>
                    <tbody>
                      {weaknesses.map((w) => (
                        <tr key={w.id} className="border-t border-[var(--line)]">
                          <td className="py-2.5">
                            <span className="font-medium">{w.student_name}</span>
                            <span className="ml-2 text-xs text-[var(--ink)]/45">{w.student_code}</span>
                          </td>
                          <td className="py-2.5">{topicLabel(w.topic)}</td>
                          <td className="py-2.5 font-semibold text-[var(--clay)]">{w.hit_count}</td>
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
                  {students.map((s) => (
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
          </section>

          <section className="mt-6 rounded-2xl border border-[var(--line)] bg-[var(--card)] p-5 backdrop-blur">
            <h2 className="text-lg font-semibold">Experimentos generados</h2>
            {experiments.length === 0 ? (
              <p className="mt-2 text-sm text-[var(--ink)]/45">Todavía no se armó ninguno.</p>
            ) : (
              <ul className="mt-4 space-y-4">
                {experiments.map((e) => (
                  <li key={e.id} className="border-t border-[var(--line)] pt-4 first:border-0 first:pt-0">
                    <p className="font-semibold">{e.title}</p>
                    <p className="text-xs text-[var(--ink)]/50">
                      {e.student_name} · {e.student_code} · {topicLabel(e.topic)}
                    </p>
                    <p className="mt-2 text-sm">
                      <span className="font-medium">Materiales:</span> {e.materials}
                    </p>
                    <p className="mt-1 whitespace-pre-line text-sm text-[var(--ink)]/80">{e.steps}</p>
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
