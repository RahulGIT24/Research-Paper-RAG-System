"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/app/lib/api";

export default function SignUpPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData(e.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      await api.post(`/auth/signup`, data);

      router.push("/signin?message=verify");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || "Failed to process request");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col space-y-6">
      <h2 className="text-3xl font-bold text-center text-slate-800">
        Create Account
      </h2>

      {error && <p className="text-red-500 text-center font-medium">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold pl-2 text-slate-600">
            Full Name
          </label>
          <input
            type="text"
            name="name"
            required
            className="w-full p-4 rounded-xl bg-slate-200 shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] focus:outline-none text-slate-700 placeholder-slate-400"
            placeholder="Rahul"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold pl-2 text-slate-600">
            Email Address
          </label>
          <input
            type="email"
            name="email"
            required
            className="w-full p-4 rounded-xl bg-slate-200 shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] focus:outline-none text-slate-700 placeholder-slate-400"
            placeholder="researcher@example.com"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold pl-2 text-slate-600">
            Password
          </label>
          <input
            type="password"
            name="password"
            required
            className="w-full p-4 rounded-xl bg-slate-200 shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] focus:outline-none text-slate-700 placeholder-slate-400"
            placeholder="••••••••"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-4 mt-4 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300 disabled:opacity-50"
        >
          {loading ? "Signing up..." : "Sign Up"}
        </button>
      </form>

      <p className="text-center text-sm text-slate-500 mt-6">
        Already have an account?{" "}
        <Link href="/signin" className="text-blue-600 font-semibold ml-1">
          Sign In
        </Link>
      </p>
    </div>
  );
}
