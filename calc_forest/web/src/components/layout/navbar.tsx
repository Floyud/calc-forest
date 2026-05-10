"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { BookOpen, ChevronDown, ClipboardCheck, Leaf, LayoutPanelTop, LogOut, Menu, ShieldCheck, TreePine, User, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/AuthProvider";

const NAV_ITEMS = [
  { href: "/", label: "工作台", icon: TreePine },
  { href: "/classroom", label: "课堂模式", icon: LayoutPanelTop },
  { href: "/diagnose", label: "诊断台", icon: ShieldCheck },
  { href: "/homework", label: "作业闭环", icon: ClipboardCheck },
];

const MORE_ITEMS = [
  { href: "/guidance", label: "引导预览", icon: BookOpen },
  { href: "/forest", label: "成长语气", icon: TreePine },
  { href: "/botanical", label: "树木百科", icon: Leaf },
];

const ALL_ITEMS = [...NAV_ITEMS, ...MORE_ITEMS];

export function Navbar() {
  const pathname = usePathname();
  const { teacher, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const anyMoreActive = MORE_ITEMS.some((item) => pathname === item.href);

  return (
    <header className="sticky top-0 z-50 border-b border-forest-200/60 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-3 text-forest-700">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-forest-200 bg-forest-50">
            <TreePine className="h-4 w-4 text-forest-600" />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold">我的计算森林</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-forest-100 text-forest-700"
                    : "text-foreground hover:bg-forest-50 hover:text-forest-700",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div ref={moreRef} className="relative">
            <button
              onClick={() => setMoreOpen((prev) => !prev)}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm transition-colors",
                anyMoreActive && !moreOpen
                  ? "bg-forest-100 text-forest-700"
                  : "text-foreground hover:bg-forest-50 hover:text-forest-700",
              )}
            >
              <span>更多</span>
              <ChevronDown
                className={cn(
                  "h-3.5 w-3.5 transition-transform duration-200",
                  moreOpen && "rotate-180",
                )}
              />
            </button>

            {moreOpen && (
              <div className="absolute right-0 top-full mt-1 min-w-[160px] rounded-lg border border-forest-200 bg-white py-1 shadow-lg">
                {MORE_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMoreOpen(false)}
                      className={cn(
                        "flex items-center gap-2 px-4 py-2 text-sm transition-colors",
                        active
                          ? "bg-forest-100 text-forest-700"
                          : "text-foreground hover:bg-forest-50 hover:text-forest-700",
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </nav>

        {teacher && (
          <div className="hidden items-center gap-2 md:flex">
            <div className="flex items-center gap-1.5 rounded-lg bg-forest-50 px-3 py-1.5 text-sm text-forest-700">
              <User className="h-3.5 w-3.5" />
              <span>{teacher.name}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-forest-50 hover:text-forest-700"
              title="退出登录"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>退出</span>
            </button>
          </div>
        )}

        <button
          className="rounded-lg border border-forest-200 p-2 text-forest-600 md:hidden"
          onClick={() => setOpen((prev) => !prev)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <nav className="border-t border-forest-200/60 bg-white/95 px-4 py-3 md:hidden">
          <div className="grid gap-1">
            {ALL_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-forest-100 text-forest-700"
                      : "text-foreground hover:bg-forest-50 hover:text-forest-700",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            {teacher && (
              <div className="mt-2 flex items-center justify-between border-t border-forest-200/60 pt-3">
                <div className="flex items-center gap-1.5 text-sm text-forest-700">
                  <User className="h-3.5 w-3.5" />
                  <span>{teacher.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-forest-50 hover:text-forest-700"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>退出</span>
                </button>
              </div>
            )}
          </div>
        </nav>
      )}
    </header>
  );
}
