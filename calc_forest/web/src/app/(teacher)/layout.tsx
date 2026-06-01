import { Navbar } from "@/components/layout/navbar";
import { DemoGuide } from "@/components/layout/DemoGuide";
import { Footer } from "@/components/layout/footer";
import { BackgroundBlobs } from "@/components/layout/BackgroundBlobs";
import { PageTransition } from "@/components/layout/PageTransition";

export default function TeacherLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="relative" style={{ zIndex: 1 }}>
      <BackgroundBlobs variant="teacher" />
      <div className="relative" style={{ zIndex: 1 }}>
        <Navbar />
        <DemoGuide />
        <PageTransition>{children}</PageTransition>
        <Footer />
      </div>
    </div>
  );
}
