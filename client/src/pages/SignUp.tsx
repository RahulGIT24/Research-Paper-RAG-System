import React, { useState } from "react";
import { AuthLayout } from "../components/AuthLayout";
import { apiCall } from "../lib/api";

export const SignUp = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
  });
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
    const data = await apiCall("/auth/signup", formData, "POST");

    setStatus({
      type: "success",
      message: "Account created! Please check your email to verify.",
    });

    setFormData({ name: "", email: "", password: "" });

  } catch (error: any) {
    const status = error?.response?.status;

    if (status === 409) {
      setStatus({
        type: "error",
        message: error?.response?.data?.error || "User already exists.",
      });
    } else {
      setStatus({
        type: "error",
        message: "Something went wrong. Please try again.",
      });
    }
  } finally {
    setLoading(false);
  }
};

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start analyzing your Notion data in seconds."
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
            Full Name
          </label>
          <input
            required
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 block w-full rounded-md border border-slate-300 py-2 px-3 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

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
          <label className="block text-sm font-medium text-slate-700">
            Password
          </label>
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
          className="flex w-full justify-center rounded-md bg-indigo-600 py-2.5 px-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 transition-colors"
        >
          {loading ? "Creating account..." : "Sign up"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Already have an account?{" "}
        <a
          href="/signin"
          className="font-semibold text-indigo-600 hover:text-indigo-500"
        >
          Sign in
        </a>
      </p>
    </AuthLayout>
  );
};
