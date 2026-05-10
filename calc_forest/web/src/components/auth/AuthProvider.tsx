"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface Teacher {
  id: string;
  name: string;
  phone: string;
  class_ids: string[];
  token: string;
}

interface AuthState {
  teacher: Teacher | null;
  loading: boolean;
  login: (teacherId?: string) => Promise<Teacher>;
  logout: () => void;
}

const STORAGE_KEY = "calc_forest_teacher";

const AuthContext = createContext<AuthState | null>(null);

/* ------------------------------------------------------------------ */
/*  API helper (inline — avoids modifying lib/api)                     */
/* ------------------------------------------------------------------ */

import { API_BASE } from "@/lib/config";

async function loginApi(teacherId?: string): Promise<Teacher> {
  const body = teacherId ? { teacher_id: teacherId } : {};
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`登录失败 (${res.status}): ${text}`);
  }
  const data = await res.json();
  return {
    id: data.teacher.id,
    name: data.teacher.name,
    phone: data.teacher.phone,
    class_ids: (data.classes ?? []).map((c: { id: string }) => c.id),
    token: data.token,
  };
}

/* ------------------------------------------------------------------ */
/*  Provider                                                           */
/* ------------------------------------------------------------------ */

const PUBLIC_PATHS = new Set(["/login"]);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [loading, setLoading] = useState(true);

  /* --- restore from localStorage on mount --- */
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        setTeacher(JSON.parse(raw) as Teacher);
      }
    } catch {
      /* corrupt data — ignore */
    }
    setLoading(false);
  }, []);

  /* --- route guard --- */
  useEffect(() => {
    if (loading) return;

    const isPublic = PUBLIC_PATHS.has(pathname);

    if (!teacher && !isPublic) {
      router.replace("/login");
    } else if (teacher && isPublic) {
      router.replace("/");
    }
  }, [teacher, loading, pathname, router]);

  /* --- login --- */
  const login = useCallback(async (teacherId?: string): Promise<Teacher> => {
    const t = await loginApi(teacherId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(t));
    setTeacher(t);
    return t;
  }, []);

  /* --- logout --- */
  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setTeacher(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthState>(
    () => ({ teacher, loading, login, logout }),
    [teacher, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
