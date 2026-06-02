import Link from 'next/link';

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="max-w-4xl w-full flex flex-col items-center text-center space-y-10">
        
        <div className="p-12 rounded-4xl bg-slate-200 shadow-[12px_12px_24px_#c1c9d2,-12px_-12px_24px_#ffffff] w-full">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-slate-800 tracking-tight">
            Research RAG Engine
          </h1>
          <p className="text-lg text-slate-600 mb-8 max-w-2xl mx-auto">
            Ingest, parse, and query complex research papers instantly. Powered by Retrieval-Augmented Generation to give you exact citations and deep insights from your academic library.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center mt-8">
            <Link 
              href="/signup" 
              className="px-8 py-4 rounded-xl font-semibold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] transition-all duration-300"
            >
              Get Started
            </Link>
            <Link 
              href="/signin" 
              className="px-8 py-4 rounded-xl font-semibold text-blue-600 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] transition-all duration-300"
            >
              Sign In
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full mt-12">
          {['Contextual Queries', 'PDF Ingestion', 'Accurate Citations'].map((feature, idx) => (
            <div key={idx} className="p-6 rounded-2xl bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] flex flex-col items-center justify-center">
              <h3 className="text-xl font-semibold text-slate-700">{feature}</h3>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}