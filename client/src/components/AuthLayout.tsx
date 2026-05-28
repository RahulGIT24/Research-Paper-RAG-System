import React from "react";

export const AuthLayout = ({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}) => {
  return (
    <div className="flex min-h-screen bg-slate-50 font-sans">
      <div className="flex flex-1 flex-col justify-center px-4 py-12 sm:px-6 lg:flex-none lg:px-20 xl:px-24 border-r border-slate-200 bg-white">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="h-8 w-8 bg-indigo-600 rounded-md flex items-center justify-center">
                <div className="h-3 w-3 bg-white rounded-full mix-blend-overlay"></div>
              </div>
              <span className="text-xl font-semibold tracking-tight text-slate-900">
                Intelligence Brain
              </span>
            </div>
            <h2 className="text-2xl font-bold leading-9 tracking-tight text-slate-900">
              {title}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">{subtitle}</p>
          </div>
          {children}
        </div>
      </div>

      <div className="relative hidden w-0 flex-1 lg:block bg-slate-900">
        <div className="absolute inset-0 flex items-center justify-center p-20">
          <div className="max-w-lg text-slate-300">
            <h3 className="text-3xl font-medium text-white mb-4">
              Connect the dots in your workspace.
            </h3>
            <p className="text-lg leading-relaxed opacity-80">
              Ingest your Notion blocks, pages, and databases. Let our engine
              synthesize your company's collective knowledge into actionable
              insights.
            </p>
          </div>
        </div>
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-size-[24px_24px]"></div>
      </div>
    </div>
  );
};
