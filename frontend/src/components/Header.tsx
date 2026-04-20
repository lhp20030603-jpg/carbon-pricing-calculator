export function Header({ backendOnline }: { backendOnline: boolean | null }) {
  const dot =
    backendOnline === null
      ? "bg-[color:var(--color-ink-300)]"
      : backendOnline
        ? "bg-[color:var(--color-brand-500)]"
        : "bg-[color:var(--color-warn-500)]";
  const label =
    backendOnline === null ? "Backend warming up…" : backendOnline ? "Backend online" : "Backend offline";
  return (
    <header className="sticky top-0 z-10 border-b border-[color:var(--color-ink-100)] bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-baseline gap-3">
          <span className="text-base font-semibold tracking-tight text-[color:var(--color-ink-900)]">
            Carbon Pricing Policy Impact Calculator
          </span>
          <span className="text-xs text-[color:var(--color-ink-500)]">
            China thermal power · 2021–2035 · reduced-form
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-[color:var(--color-ink-500)]">
          <span className="flex items-center gap-1.5">
            <span className={`inline-block h-2 w-2 rounded-full ${dot}`} aria-hidden />
            {label}
          </span>
          <a
            href="https://github.com/"
            className="hover:text-[color:var(--color-brand-600)]"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
          <a
            href="/docs/methodology.pdf"
            className="hover:text-[color:var(--color-brand-600)]"
            target="_blank"
            rel="noreferrer"
          >
            Methodology
          </a>
        </div>
      </div>
    </header>
  );
}
