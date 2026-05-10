import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    optimizePackageImports: ["framer-motion", "lucide-react", "recharts"],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000"}/health`,
      },
    ];
  },
};

export default nextConfig;
