"use client";

import { useEffect } from "react";
import { logger } from "@/lib/logger";

export default function TeacherError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logger.error("error_boundary", { location: "teacher", message: error.message, digest: error.digest, stack: error.stack });
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">🍎</div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          功能暂时不可用
        </h2>
        <p className="text-gray-500 mb-6">
          教师端遇到了一个小问题，请刷新页面重试。
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors font-medium"
          >
            重新加载
          </button>
          <a
            href="/"
            className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium"
          >
            返回首页
          </a>
        </div>
      </div>
    </div>
  );
}
