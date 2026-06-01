import type { ReactNode } from "react";
import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function WorkspacePage({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto flex w-full max-w-[1440px] flex-col gap-8 px-5 py-8 md:px-8 md:py-10", className)}>
      {children}
    </div>
  );
}

export function PageHero({
  eyebrow,
  title,
  description,
  metric,
  actions,
  aside,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  metric?: { label: string; value: string; note?: string };
  actions?: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section className="surface-hero grid gap-6 overflow-hidden rounded-[24px] px-5 py-6 md:px-8 md:py-7 xl:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.9fr)]">
      <div className="relative z-10 flex flex-col gap-4">
        {eyebrow ? (
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--tone-muted)]">
            {eyebrow}
          </p>
        ) : null}
        <div className="space-y-2.5">
          <h1 className="max-w-4xl text-2xl font-semibold tracking-tight text-[var(--tone-ink)] md:text-4xl">
            {title}
          </h1>
          <p className="max-w-3xl text-sm leading-7 text-muted-foreground">
            {description}
          </p>
        </div>
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : <div />}
          {metric ? (
            <div className="min-w-[180px] rounded-[18px] border border-white/60 bg-white/70 px-4 py-3 backdrop-blur-sm">
              <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--tone-muted)]">{metric.label}</p>
              <p className="mt-1.5 text-2xl font-semibold tracking-tight text-[var(--tone-ink)]">{metric.value}</p>
              {metric.note ? <p className="mt-1 text-[11px] text-muted-foreground">{metric.note}</p> : null}
            </div>
          ) : null}
        </div>
      </div>
      {aside ? (
        <div className="relative z-10 flex min-h-full flex-col justify-end">
          <div className="surface-panel h-full rounded-[20px] p-5 md:p-6">{aside}</div>
        </div>
      ) : null}
    </section>
  );
}

export function SectionPanel({
  title,
  description,
  action,
  children,
  className,
  contentClassName,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  return (
    <Card className={cn("surface-panel gap-0 rounded-[20px] border-0 shadow-none", className)}>
      <CardHeader className="border-b border-[var(--tone-line)] px-5 py-4 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base font-semibold tracking-tight text-[var(--tone-ink)]">{title}</CardTitle>
            {description ? <CardDescription className="text-[13px]">{description}</CardDescription> : null}
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent className={cn("px-5 pt-5 md:px-6", contentClassName)}>{children}</CardContent>
    </Card>
  );
}

export function MetricCard({
  label,
  value,
  note,
  icon,
  emphasis = "default",
}: {
  label: string;
  value: string;
  note: string;
  icon?: ReactNode;
  emphasis?: "default" | "warm" | "success";
}) {
  return (
    <div
      className={cn(
        "rounded-[20px] border px-4 py-3.5",
        emphasis === "default" && "border-[var(--tone-line)] bg-white/86",
        emphasis === "warm" && "border-[var(--tone-accent)] bg-[var(--tone-soft)]",
        emphasis === "success" && "border-emerald-200 bg-emerald-50/90",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--tone-muted)]">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-[var(--tone-ink)]">{value}</p>
        </div>
        {icon ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-[12px] bg-[var(--tone-soft)]">
            <span className="text-base text-[var(--tone-accent-strong)]">{icon}</span>
          </div>
        ) : null}
      </div>
      <p className="mt-2 text-[13px] leading-6 text-muted-foreground">{note}</p>
    </div>
  );
}

export function InsightStrip({
  title,
  value,
  detail,
  tone = "default",
}: {
  title: string;
  value: string;
  detail?: string;
  tone?: "default" | "warn" | "success";
}) {
  return (
    <div
      className={cn(
        "rounded-[18px] border px-3.5 py-2.5",
        tone === "default" && "border-[var(--tone-line)] bg-white/70",
        tone === "warn" && "border-amber-200 bg-amber-50/90",
        tone === "success" && "border-emerald-200 bg-emerald-50/90",
      )}
    >
      <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--tone-muted)]">{title}</p>
      <p className="mt-1 text-sm font-medium text-[var(--tone-ink)]">{value}</p>
      {detail ? <p className="mt-1 text-[13px] text-muted-foreground">{detail}</p> : null}
    </div>
  );
}

export function ActionRail({
  title,
  description,
  items,
}: {
  title: string;
  description?: string;
  items: Array<{ label: string; description: string; href: string; icon?: ReactNode }>;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-base font-semibold tracking-tight text-[var(--tone-ink)]">{title}</h2>
        {description ? <p className="text-[13px] text-muted-foreground">{description}</p> : null}
      </div>
      <div className="grid gap-3">
        {items.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="group rounded-[20px] border border-[var(--tone-line)] bg-white/80 px-4 py-3.5 transition-all duration-300 hover:-translate-y-[2px] hover:border-[var(--tone-accent)] hover:bg-white hover:shadow-sm"
            style={{
              transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            <div className="flex items-start gap-3">
              {item.icon ? (
                <div className="mt-0.5 flex size-10 items-center justify-center rounded-[14px] bg-[var(--tone-soft)] text-[var(--tone-accent-strong)] transition-transform duration-300 group-hover:scale-[1.04]">
                  {item.icon}
                </div>
              ) : null}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[var(--tone-ink)]">{item.label}</span>
                  <ArrowRight className="h-3.5 w-3.5 text-[var(--tone-muted)] transition-transform duration-300 group-hover:translate-x-[3px]" />
                </div>
                <p className="mt-1 text-[13px] leading-6 text-muted-foreground">{item.description}</p>
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

export function ReviewStatusBadge({
  status,
  label,
}: {
  status: "pending" | "reviewed";
  label?: string;
}) {
  const pending = status === "pending";
  return (
    <Badge
      className={cn(
        "h-6 rounded-full px-2.5 text-[10px] font-semibold tracking-[0.12em] uppercase",
        pending
          ? "bg-sky-50 text-sky-700 ring-1 ring-sky-200"
          : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
      )}
    >
      {label ?? (pending ? "待教师审核" : "教师已确认")}
    </Badge>
  );
}

export function HeroActionButton({
  href,
  children,
  variant = "default",
}: {
  href: string;
  children: ReactNode;
  variant?: "default" | "outline";
}) {
  return (
    <a
      href={href}
      className={cn(
        "group/button inline-flex h-9 shrink-0 items-center justify-center gap-1.5 rounded-full border border-transparent px-4 text-[13px] font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:translate-y-px [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        "h-9 rounded-full px-4 text-[13px]",
        variant === "default" && "bg-[var(--tone-accent-strong)] text-white hover:bg-[color:color-mix(in_oklab,var(--tone-accent-strong)_88%,black)]",
        variant === "outline" && "border-[var(--tone-line)] bg-white/85 text-[var(--tone-ink)] hover:bg-white",
      )}
    >
      {children}
    </a>
  );
}
