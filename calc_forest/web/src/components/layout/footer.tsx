import { ClipboardCheck, Flame, ShieldCheck, TreePine } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-[color:var(--tone-line)] bg-[rgba(252,248,239,0.72)] backdrop-blur-sm">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-6 md:flex-row md:items-center md:justify-between md:px-6">
        <div className="flex items-center gap-2 text-[var(--tone-ink)]">
          <TreePine className="h-4 w-4 text-[var(--tone-accent-strong)]" />
          <span className="text-[13px] font-medium tracking-tight">我的计算森林</span>
        </div>

        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-[var(--tone-muted)]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3 w-3 text-[var(--tone-accent-strong)]" />
            全部输出待教师审核
          </span>
          <span aria-hidden="true" className="text-[var(--tone-muted)]/40 select-none">·</span>
          <span className="flex items-center gap-1.5">
            <ClipboardCheck className="h-3 w-3 text-[var(--tone-accent-strong)]" />
            作业、课堂、诊断共用同一教师工作流
          </span>
          <span aria-hidden="true" className="text-[var(--tone-muted)]/40 select-none">·</span>
          <span className="flex items-center gap-1.5">
            <Flame className="h-3 w-3 text-[var(--tone-accent)]" />
            教师端演示
          </span>
        </div>
      </div>
    </footer>
  );
}
