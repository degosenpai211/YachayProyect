import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchHealth, telegramDeepLink } from "../api.js";

const HERO_IMG =
  "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1920&q=80";

export default function Landing() {
  const [bot, setBot] = useState(import.meta.env.VITE_TELEGRAM_BOT || "YachayBot");

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        if (h.telegram_bot) setBot(h.telegram_bot);
      })
      .catch(() => {});
  }, []);

  const studentLink = telegramDeepLink(bot, "UEBOL-3A-12");

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center animate-[kenburns_18s_ease-in-out_infinite_alternate]"
        style={{ backgroundImage: `url(${HERO_IMG})` }}
        aria-hidden
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(105deg, rgba(30,77,40,0.88) 0%, rgba(30,77,40,0.55) 45%, rgba(26,46,31,0.25) 100%)",
        }}
      />

      <header className="relative z-10 flex items-center justify-between px-6 py-5 md:px-12">
        <span className="brand text-2xl font-bold tracking-tight text-white">Yachay</span>
        <Link
          to="/dashboard"
          className="text-sm font-medium text-white/80 transition hover:text-white"
        >
          Dashboard docente
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-80px)] max-w-5xl flex-col justify-center px-6 pb-16 md:px-12">
        <p className="animate-rise brand text-5xl font-bold leading-none text-white md:text-7xl md:leading-none">
          Yachay
        </p>
        <h1 className="animate-rise-delay mt-5 max-w-xl text-2xl font-semibold leading-snug text-white md:text-3xl">
          Tutor de ciencias por Telegram, con ejemplos bolivianos.
        </h1>
        <p className="animate-rise-delay mt-4 max-w-lg text-base text-white/85 md:text-lg">
          El alumno pregunta por chat; detectamos en qué flaquea y, si hace falta, armamos un
          mini-experimento casero. Tú lo ves en el dashboard.
        </p>

        <div className="animate-rise-delay mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
          <a
            href={studentLink}
            target="_blank"
            rel="noreferrer"
            className="animate-pulse-soft inline-flex items-center justify-center rounded-xl bg-[var(--sun)] px-7 py-3.5 text-base font-semibold text-[var(--ink)] shadow-lg transition hover:brightness-105"
          >
            Abrir en Telegram
          </a>
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-xl border border-white/40 bg-white/10 px-7 py-3.5 text-base font-semibold text-white backdrop-blur transition hover:bg-white/20"
          >
            Dashboard docente
          </Link>
        </div>

        <p className="mt-8 text-sm text-white/70">
          Al entrar, escribe tu código (ej. <code className="text-[var(--sun)]">UEBOL-3A-12</code>).
        </p>
      </main>
    </div>
  );
}
