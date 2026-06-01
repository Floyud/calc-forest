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

const DEFAULT_TEACHER: Teacher = {
  id: "T001",
  name: "张老师",
  phone: "13800000001",
  class_ids: ["C001"],
  token: "dev-local",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        setTeacher(JSON.parse(raw) as Teacher);
      } else {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_TEACHER));
        setTeacher(DEFAULT_TEACHER);
      }
    } catch {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_TEACHER));
      setTeacher(DEFAULT_TEACHER);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (loading || !teacher) return;
    if (pathname.startsWith("/s")) return;
    if (pathname === "/login") {
      router.replace("/");
    }
  }, [teacher, loading, pathname, router]);

  const login = useCallback(async (): Promise<Teacher> => {
    setTeacher(DEFAULT_TEACHER);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_TEACHER));
    return DEFAULT_TEACHER;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setTeacher(DEFAULT_TEACHER);
  }, [router]);

  const value = useMemo<AuthState>(
    () => ({ teacher, loading, login, logout }),
    [teacher, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
