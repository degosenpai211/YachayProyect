export default function StatCard({ label, value, accent = false }) {
  return (
    <div className="rounded-2xl border border-[var(--line)] bg-[var(--card)] p-4 backdrop-blur md:p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--ink)]/50">{label}</p>
      <p
        className={`mt-1 text-3xl font-bold tabular-nums ${
          accent ? "text-[var(--clay)]" : "text-[var(--leaf-deep)]"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
