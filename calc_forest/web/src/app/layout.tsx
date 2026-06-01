import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { TreeDefs } from "@/components/forest/trees/TreeDefs";
import { QueryProvider } from "@/lib/api/provider";

export const metadata: Metadata = {
  title: "我的计算森林",
  description:
    "教师主导的小学数学错因诊断、课堂练习与审核工作台。",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <head />
      <body className="bg-background text-foreground overscroll-none">
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded focus:bg-white focus:px-4 focus:py-2 focus:shadow-lg">
          跳到主要内容
        </a>
        <TreeDefs />
        <QueryProvider>
          <AuthProvider>
            <main id="main-content" className="relative flex-1 min-h-dvh">{children}</main>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
