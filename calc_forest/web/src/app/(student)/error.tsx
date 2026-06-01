"use client";

import { useEffect } from "react";
import { logger } from "@/lib/logger";

export default function StudentError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logger.error("error_boundary", { location: "student", message: error.message, digest: error.digest, stack: error.stack });
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">🌱</div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          哎呀，出了点小问题
        </h2>
        <p className="text-gray-500 mb-6">
          小树苗遇到了一点麻烦，刷新一下就好了。
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors font-medium"
          >
            重新加载
          </button>
          <a
            href="/s/home"
            className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium"
          >
            返回首页
          </a>
        </div>
      </div>
    </div>
  );
}
