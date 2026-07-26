import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchHealth, telegramDeepLink } from "../api.js";

export default function Landing() {
  const [bot, setBot] = useState(import.meta.env.VITE_TELEGRAM_BOT || "YachayBot");

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        if (h.telegram_bot) setBot(h.telegram_bot);
      })
      .catch(() => {});
  }, []);

  const studentLink = telegramDeepLink(bot, "UEBOL-3A");

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%232f6b3a' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        }}
      />

      <header className="relative z-10 flex items-center justify-between px-6 py-5 md:px-12">
        <span className="brand text-2xl font-bold tracking-tight text-[var(--leaf-deep)]">Yachay</span>
        <Link
          to="/dashboard"
          className="text-sm font-medium text-[var(--ink)]/70 hover:text-[var(--leaf)] transition"
        >
          Dashboard docente
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-80px)] max-w-5xl flex-col justify-center px-6 pb-16 md:px-12">
        <p className="animate-rise brand text-5xl font-bold leading-none text-[var(--leaf-deep)] md:text-7xl md:leading-none">
          Yachay
        </p>
        <h1 className="animate-rise-delay mt-5 max-w-xl text-2xl font-semibold leading-snug text-[var(--ink)] md:text-3xl">
          Tu tutor de ciencias por Telegram, con ejemplos bolivianos.
        </h1>
        <p className="animate-rise-delay mt-4 max-w-lg text-base text-[var(--ink)]/75 md:text-lg">
          Pregunta por voz o texto. Detectamos en qué flaqueas y, cuando hace falta, armamos un
          mini-experimento casero. Tu profe lo ve en el dashboard.
        </p>

        <div className="animate-rise-delay mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
          <a
            href={studentLink}
            target="_blank"
            rel="noreferrer"
            className="animate-pulse-soft inline-flex items-center justify-center rounded-xl bg-[var(--leaf)] px-7 py-3.5 text-base font-semibold text-white shadow-lg shadow-[var(--leaf)]/25 transition hover:bg-[var(--leaf-deep)]"
          >
            Asistencia básica
          </a>
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-xl border border-[var(--line)] bg-white/60 px-7 py-3.5 text-base font-semibold text-[var(--ink)] backdrop-blur transition hover:bg-white"
          >
            Dashboard docente
          </Link>
        </div>

        <p className="mt-8 text-sm text-[var(--ink)]/50">
          Al entrar, escribe tu código (ej. <code className="text-[var(--clay)]">UEBOL-3A-12</code>).
        </p>
      </main>
    </div>
  );
}
