import React, { useState } from "react";
import { AuthLayout } from "../components/AuthLayout";
import { apiCall } from "../lib/api";

export const SignIn = () => {
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [status, setStatus] = useState<{
    type: "error" | "info" | null;
    message: string;
  }>({ type: null, message: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: null, message: "" });

    try {
      const data = await apiCall("/auth/signin", formData, "POST");

      if (data.message === "User not verified, verification email sent") {
        setStatus({
          type: "info",
          message:
            "Account not verified. A new verification email has been sent.",
        });
        return;
      }

      window.location.href = "/dashboard";
    } catch (error: any) {
      const status = error?.status;

      if (status === 401) {
        setStatus({
          type: "error",
          message: "Invalid email or password.",
        });
      } else {
        setStatus({
          type: "error",
          message: "An unexpected error occurred.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Sign in to your account"
      subtitle="Welcome back to Intelligence Brain."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {status.type && (
          <div
            className={`p-3 text-sm rounded-md border ${status.type === "error" ? "bg-red-50 text-red-600 border-red-200" : "bg-blue-50 text-blue-700 border-blue-200"}`}
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
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            className="mt-1 block w-full rounded-md border border-slate-300 py-2 px-3 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <a
              href="/forgot-password"
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-500"
            >
              Forgot password?
            </a>
          </div>
          <input
            required
            type="password"
            value={formData.password}
            onChange={(e) =>
              setFormData({ ...formData, password: e.target.value })
            }
            className="mt-1 block w-full rounded-md border border-slate-300 py-2 px-3 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <button
          disabled={loading}
          type="submit"
          className="flex w-full justify-center rounded-md bg-slate-900 py-2.5 px-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 focus-visible:outline  focus-visible:outline-offset-2 focus-visible:outline-slate-900 disabled:opacity-50 transition-colors"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Don't have an account?{" "}
        <a
          href="/signup"
          className="font-semibold text-indigo-600 hover:text-indigo-500"
        >
          Sign up
        </a>
      </p>
    </AuthLayout>
  );
};
