"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8">
      <h2 className="text-xl font-bold text-bark-800">出了点问题</h2>
      <p className="text-sm text-muted-foreground">页面加载时遇到了一个错误</p>
      <button
        onClick={reset}
        className="rounded-lg bg-forest-600 px-4 py-2 text-sm text-white hover:bg-forest-700"
      >
        重试
      </button>
    </div>
  );
}
