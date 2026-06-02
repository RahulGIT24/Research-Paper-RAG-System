export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-200">
      <div className="w-full max-w-md p-8 rounded-4xl bg-slate-200 shadow-[12px_12px_24px_#c1c9d2,-12px_-12px_24px_#ffffff]">
        {children}
      </div>
    </div>
  );
}