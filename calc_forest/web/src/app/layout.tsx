import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/navbar";
import { DemoGuide } from "@/components/layout/DemoGuide";
import { Footer } from "@/components/layout/footer";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { TreeDefs } from "@/components/forest/trees/TreeDefs";
import { QueryProvider } from "@/lib/api/provider";

export const metadata: Metadata = {
  title: "我的计算森林",
  description:
    "教师主导的小学数学错因诊断、课堂练习与审核工作台。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="bg-background text-foreground">
        <TreeDefs />
        <QueryProvider>
          <AuthProvider>
            <Navbar />
            <DemoGuide />
            <main className="flex-1">{children}</main>
            <Footer />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
