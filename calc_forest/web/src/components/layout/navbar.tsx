"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, LogOut, Menu, Sparkles, TreePine, User, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/AuthProvider";
import { PRIMARY_NAV_ITEMS, SECONDARY_NAV_ITEMS } from "@/lib/presentation";

const ALL_ITEMS = [...PRIMARY_NAV_ITEMS, ...SECONDARY_NAV_ITEMS];

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

  const anyMoreActive = SECONDARY_NAV_ITEMS.some((item) => pathname === item.href);

  return (
    <header className="sticky top-0 z-50 border-b border-[color:var(--tone-line)] bg-[rgba(252,248,239,0.8)] backdrop-blur-xl shadow-[0_1px_2px_rgba(90,84,60,0.04)]">
      <div className="mx-auto flex h-[72px] w-full max-w-[1440px] items-center justify-between gap-4 px-4 md:px-6">
        <Link href="/" className="flex min-w-0 items-center gap-2.5 text-[var(--tone-ink)]">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[color:var(--tone-line)] bg-white/70 shadow-[0_2px_8px_rgba(90,84,60,0.05)]">
            <TreePine className="h-[17px] w-[17px] text-[var(--tone-accent-strong)]" />
          </div>
          <div className="min-w-0">
            <div className="text-[13px] font-semibold tracking-tight leading-none">我的计算森林</div>
            <div className="mt-1 text-[11px] leading-none text-[var(--tone-muted)]">教师工作台</div>
          </div>
        </Link>

        <nav aria-label="主导航" className="hidden items-center gap-1 lg:flex">
          {PRIMARY_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-[background-color,color,box-shadow] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]",
                  active
                    ? "bg-[var(--tone-paper-strong)] text-[var(--tone-ink)] shadow-[0_1px_3px_rgba(90,84,60,0.05)] ring-1 ring-[color:var(--tone-line)]"
                    : "text-[var(--tone-muted)] hover:bg-white/70 hover:text-[var(--tone-ink)]",
                )}
                title={item.description}
              >
                <Icon className="h-[15px] w-[15px]" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div ref={moreRef} className="relative">
            <button
              onClick={() => setMoreOpen((prev) => !prev)}
              className={cn(
                "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-[background-color,color,box-shadow] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]",
                anyMoreActive && !moreOpen
                  ? "bg-[var(--tone-paper-strong)] text-[var(--tone-ink)] shadow-[0_1px_3px_rgba(90,84,60,0.05)] ring-1 ring-[color:var(--tone-line)]"
                  : "text-[var(--tone-muted)] hover:bg-white/70 hover:text-[var(--tone-ink)]",
              )}
            >
              <Sparkles className="h-[15px] w-[15px]" />
              <span>品牌与演示</span>
              <ChevronDown
                className={cn(
                  "h-3 w-3 transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]",
                  moreOpen && "rotate-180",
                )}
              />
            </button>

            {moreOpen && (
              <div
                className="absolute right-0 top-full mt-1 min-w-[260px] rounded-2xl border border-[color:var(--tone-line)] bg-[rgba(255,252,245,0.98)] p-1.5 shadow-[0_12px_32px_rgba(90,84,60,0.1)]"
                style={{ animation: "smooth-fade-in 0.18s cubic-bezier(0.16,1,0.3,1)" }}
              >
                {SECONDARY_NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMoreOpen(false)}
                      className={cn(
                        "flex items-start gap-3 rounded-xl px-3 py-2.5 transition-[background-color,color] duration-200",
                        active
                          ? "bg-[var(--tone-soft)] text-[var(--tone-ink)]"
                          : "text-[var(--tone-ink)] hover:bg-[var(--tone-soft)]/70",
                      )}
                    >
                      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/80 text-[var(--tone-accent-strong)] ring-1 ring-[color:var(--tone-line)]">
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="space-y-0.5">
                        <span className="block text-[13px] font-medium leading-snug">{item.label}</span>
                        <span className="block text-[11px] leading-snug text-[var(--tone-muted)]">{item.description}</span>
                      </span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </nav>

        {teacher && (
          <div className="hidden items-center gap-1.5 lg:flex">
            <div className="flex items-center gap-2 rounded-full border border-[color:var(--tone-line)] bg-white/60 px-3 py-1.5 text-[13px] font-medium text-[var(--tone-ink)]">
              <User className="h-3.5 w-3.5 text-[var(--tone-muted)]" />
              <span>{teacher.name}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[13px] font-medium text-[var(--tone-muted)] transition-[color,background-color] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] hover:bg-white/70 hover:text-[var(--tone-ink)]"
              title="退出登录"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>退出</span>
            </button>
          </div>
        )}

        <button
          className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-[color:var(--tone-line)] bg-white/70 p-2.5 text-[var(--tone-accent-strong)] transition-colors duration-300 hover:bg-white/90 active:scale-[0.96] active:transition-transform active:duration-100 lg:hidden"
          onClick={() => setOpen((prev) => !prev)}
          aria-label="切换菜单"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <nav
          aria-label="主导航"
          className="border-t border-[color:var(--tone-line)] bg-[rgba(255,252,245,0.96)] backdrop-blur-lg px-4 py-3 lg:hidden"
          style={{ animation: "smooth-fade-in 0.25s cubic-bezier(0.16,1,0.3,1)" }}
        >
          <div className="grid gap-0.5">
            {ALL_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "stagger-item flex min-h-[44px] items-center gap-3 rounded-2xl px-3 py-2.5 transition-[background-color,color] duration-200",
                    active
                      ? "bg-[var(--tone-soft)] text-[var(--tone-ink)]"
                      : "text-[var(--tone-ink)] hover:bg-white/80 active:bg-white/60",
                  )}
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-[color:var(--tone-line)] bg-white/80 text-[var(--tone-accent-strong)]">
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="space-y-0.5">
                    <span className="block text-[13px] font-medium leading-snug">{item.shortLabel ?? item.label}</span>
                    <span className="block text-[11px] leading-snug text-[var(--tone-muted)]">{item.description}</span>
                  </span>
                </Link>
              );
            })}
            {teacher && (
              <div className="stagger-item mt-2 flex items-center justify-between border-t border-[color:var(--tone-line)] pt-3">
                <div className="flex items-center gap-1.5 text-[13px] font-medium text-[var(--tone-ink)]">
                  <User className="h-3.5 w-3.5 text-[var(--tone-muted)]" />
                  <span>{teacher.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex min-h-[36px] items-center gap-1.5 rounded-full px-3 py-1.5 text-[13px] font-medium text-[var(--tone-muted)] transition-[color,background-color] duration-200 hover:bg-white/80 hover:text-[var(--tone-ink)] active:bg-white/60"
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
