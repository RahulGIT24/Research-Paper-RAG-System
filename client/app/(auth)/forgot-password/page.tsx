"use client";

import { useState } from "react";
import Link from "next/link";
import axios from "axios";
import { api } from "@/app/lib/api";

export default function ForgotPasswordPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus("loading");

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email");

    try {
      const res = await api.post(`/auth/forgot-password`, { email });

      setStatus("success");
      setMessage(res.data.message || "Forgot password email sent successfully");
    } catch (err) {
      setStatus("error");

      if (axios.isAxiosError(err)) {
        setMessage(err.response?.data?.error || "Failed to process request");
      }
      else if (err instanceof Error) {
        setMessage(err.message);
      }
      else {
        setMessage("An unexpected error occurred");
      }
    }
  };

  return (
    <div className="flex flex-col space-y-6">
      <h2 className="text-3xl font-bold text-center text-slate-800">Reset Password</h2>
      <p className="text-center text-slate-600 text-sm">
        Enter your email to receive a password reset link.
      </p>

      {status === "error" && <p className="text-red-500 text-center font-medium">{message}</p>}
      {status === "success" && <p className="text-green-600 text-center font-medium">{message}</p>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold pl-2 text-slate-600">Email Address</label>
          <input
            type="email"
            name="email"
            required
            className="w-full p-4 rounded-xl bg-slate-200 shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] focus:outline-none text-slate-700 placeholder-slate-400"
            placeholder="researcher@example.com"
          />
        </div>

        <button
          type="submit"
          disabled={status === "loading"}
          className="w-full py-4 mt-4 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300 disabled:opacity-50"
        >
          {status === "loading" ? "Sending..." : "Send Reset Link"}
        </button>
      </form>

      <div className="text-center mt-6">
        <Link href="/signin" className="text-sm text-slate-500 hover:text-slate-700 transition-colors">
          &larr; Back to Sign In
        </Link>
      </div>
    </div>
  );
}