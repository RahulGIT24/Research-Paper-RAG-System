"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import toast from "react-hot-toast";

interface UserProfile {
    name?: string;
    email?: string;
    [key: string]: unknown;
}

export default function TopNav() {
    const router = useRouter();
    const [user, setUser] = useState<UserProfile | null>(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await axios.get(process.env.NEXT_PUBLIC_API_URL + "/user/", { withCredentials: true });
                setUser(res.data);
            } catch (err) {
                if (axios.isAxiosError(err) && err.response?.status === 401) {
                    router.push("/signin");
                }
            }
        };
        fetchUser();
    }, [router]);

    const handleLogout = async () => {
        try {
            await axios.post(process.env.NEXT_PUBLIC_API_URL + "/auth/logout", {},{ withCredentials: true });
            toast.success("Logged Out Successfully")
            router.push("/signin");
        } catch (err) {
            console.log(err)
        }
    };

    return (
        <header className="p-4 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] mb-8 sticky top-0 z-10">
            <div className="max-w-6xl mx-auto flex justify-between items-center">
                <h1 className="text-2xl font-bold text-slate-800 tracking-tight">RAG Dashboard</h1>

                <div className="flex items-center space-x-6">
                    <div className="text-slate-600 font-medium">
                        {user ? `Hello, ${user.name || user.email}` : "Loading..."}
                    </div>

                    <button
                        onClick={()=>router.push("/dashboard/query")}
                        className="px-6 py-2 rounded-xl font-bold text-blue-500 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300"
                    >
                        Query
                    </button>
                    <button
                        onClick={handleLogout}
                        className="px-6 py-2 rounded-xl font-bold text-red-500 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300"
                    >
                        Logout
                    </button>
                </div>
            </div>
        </header>
    );
}