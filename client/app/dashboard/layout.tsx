import TopNav from "./TopNav";
import { Toaster } from 'react-hot-toast';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-slate-200 flex flex-col">
            <TopNav />
            <main className="flex-1 w-full max-w-6xl mx-auto p-6">
                {children}
            </main>
            <Toaster position="bottom-center" />
        </div>
    );
}