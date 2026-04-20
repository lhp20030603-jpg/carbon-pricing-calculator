/**
 * Small stateless primitives shared across panels. Tailwind only — no runtime
 * state here.
 */

import clsx from "clsx";
import type { ReactNode } from "react";

export function Card({
  children,
  className,
  as: As = "section",
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  as?: "section" | "div" | "aside";
  padded?: boolean;
}) {
  return (
    <As
      className={clsx(
        "rounded-xl border border-[color:var(--color-ink-100)] bg-white shadow-sm",
        padded && "p-4",
        className,
      )}
    >
      {children}
    </As>
  );
}

export function SectionTitle({
  title,
  help,
  className,
}: {
  title: string;
  help?: string;
  className?: string;
}) {
  return (
    <div className={clsx("mb-2 flex items-start justify-between gap-2", className)}>
      <h2 className="text-sm font-semibold tracking-tight text-[color:var(--color-ink-900)]">
        {title}
      </h2>
      {help ? (
        <span
          aria-label={help}
          title={help}
          className="cursor-help text-xs text-[color:var(--color-ink-500)]"
        >
          ⓘ
        </span>
      ) : null}
    </div>
  );
}

export function Pill({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "brand" | "warn" | "crit";
}) {
  const cls = {
    neutral: "bg-[color:var(--color-ink-100)] text-[color:var(--color-ink-700)]",
    brand: "bg-[color:var(--color-brand-100)] text-[color:var(--color-brand-600)]",
    warn: "bg-[color:var(--color-warn-100)] text-[color:var(--color-warn-500)]",
    crit: "bg-[color:var(--color-crit-100)] text-[color:var(--color-crit-500)]",
  }[tone];
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        cls,
      )}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
  className,
  title,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
  title?: string;
}) {
  const base =
    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 px-3 py-2";
  const variants = {
    primary:
      "bg-[color:var(--color-brand-600)] text-white hover:bg-[color:var(--color-brand-500)]",
    secondary:
      "border border-[color:var(--color-ink-300)] bg-white text-[color:var(--color-ink-900)] hover:bg-[color:var(--color-ink-100)]",
    ghost: "text-[color:var(--color-ink-700)] hover:bg-[color:var(--color-ink-100)]",
  }[variant];
  return (
    <button
      type={type}
      title={title}
      onClick={onClick}
      disabled={disabled}
      className={clsx(base, variants, className)}
    >
      {children}
    </button>
  );
}

export function LabeledValue({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col">
      <span className="text-xs uppercase tracking-wide text-[color:var(--color-ink-500)]">
        {label}
      </span>
      <span className="mt-1 text-lg font-semibold tabular-nums text-[color:var(--color-ink-900)]">
        {value}
      </span>
      {hint ? (
        <span className="text-xs text-[color:var(--color-ink-500)]">{hint}</span>
      ) : null}
    </div>
  );
}
