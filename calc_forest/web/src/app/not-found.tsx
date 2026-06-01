import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">🌿</div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          页面不存在
        </h2>
        <p className="text-gray-500 mb-6">
          这棵小树还没长到这里，请检查地址是否正确。
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors font-medium"
        >
          返回首页
        </Link>
      </div>
    </div>
  );
}
