"use client";

import { useEffect } from "react";
import { logger } from "@/lib/logger";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logger.error("error_boundary", { location: "global", message: error.message, digest: error.digest, stack: error.stack });
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">🌳</div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          页面出了点问题
        </h2>
        <p className="text-gray-500 mb-6">
          别担心，小树会重新长好的。请尝试刷新页面。
        </p>
        <button
          onClick={reset}
          className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors font-medium"
        >
          重新加载
        </button>
      </div>
    </div>
  );
}
