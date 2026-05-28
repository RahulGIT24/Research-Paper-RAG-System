import React, { useState } from "react";
import { AuthLayout } from "../components/AuthLayout";
import { apiCall } from "../lib/api";

export const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<{
    type: "error" | "success" | null;
    message: string;
  }>({ type: null, message: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setStatus({ type: null, message: "" });

  try {
    await apiCall("/auth/forgot-password", { email }, "POST");

    setStatus({
      type: "success",
      message: "If an account exists, a reset link has been sent.",
    });

    setEmail("");

  } catch (error: any) {
    const status = error?.status;

    if (status === 404) {
      setStatus({
        type: "error",
        message: "User not found.",
      });
    } else {
      setStatus({
        type: "error",
        message: "Failed to process request.",
      });
    }
  } finally {
    setLoading(false);
  }
};

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your email to receive a reset link."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {status.type && (
          <div
            className={`p-3 text-sm rounded-md border ${status.type === "error" ? "bg-red-50 text-red-600 border-red-200" : "bg-green-50 text-green-700 border-green-200"}`}
          >
            {status.message}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700">
            Email address
          </label>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 py-2 px-3 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <button
          disabled={loading || status.type === "success"}
          type="submit"
          className="flex w-full justify-center rounded-md bg-slate-900 py-2.5 px-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-slate-900 disabled:opacity-50 transition-colors"
        >
          {loading ? "Sending link..." : "Send reset link"}
        </button>
      </form>
      <div className="mt-6 text-center">
        <a
          href="/signin"
          className="text-sm font-semibold text-slate-600 hover:text-slate-900"
        >
          &larr; Back to sign in
        </a>
      </div>
    </AuthLayout>
  );
};
