"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function ResetClient({ token }: { token: string }) {
  const router = useRouter();
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!token) {
      setStatus("error");
      setMessage("Invalid or missing reset token.");
      return;
    }

    setStatus("loading");

    const formData = new FormData(e.currentTarget);
    const new_password = formData.get("new_password");

    try {
      const res = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/reset-password`,
        {
          token,
          new_password,
        },
      );

      setStatus("success");
      setMessage(res.data.message || "Password reset successfully");

      setTimeout(() => {
        router.push("/signin");
      }, 2000);
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
      <h2 className="text-3xl font-bold text-center text-slate-800">
        Set New Password
      </h2>

      {status === "error" && (
        <p className="text-red-500 text-center font-medium">{message}</p>
      )}
      {status === "success" && (
        <p className="text-green-600 text-center font-medium">{message}</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold pl-2 text-slate-600">
            New Password
          </label>
          <input
            type="password"
            name="new_password"
            required
            className="w-full p-4 rounded-xl bg-slate-200 shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] focus:outline-none text-slate-700 placeholder-slate-400"
            placeholder="••••••••"
          />
        </div>

        <button
          type="submit"
          disabled={status === "loading" || status === "success"}
          className="w-full py-4 mt-4 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300 disabled:opacity-50"
        >
          {status === "loading" ? "Updating..." : "Update Password"}
        </button>
      </form>
    </div>
  );
}
