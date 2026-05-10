export default function NotFound() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8">
      <h2 className="text-xl font-bold text-bark-800">页面未找到</h2>
      <a href="/" className="text-sm text-forest-600 hover:underline">
        返回首页
      </a>
    </div>
  );
}
