import { Flame, ShieldCheck, TreePine } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-forest-200 bg-white/60">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-foreground">
          <TreePine className="h-4 w-4 text-forest-600" />
          <span>我的计算森林</span>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-forest-500" />
            全部输出待教师审核
          </span>
          <span className="flex items-center gap-1.5">
            <Flame className="h-3.5 w-3.5 text-warm-400" />
            教师端演示
          </span>
        </div>
      </div>
    </footer>
  );
}
