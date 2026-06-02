"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";

export default function VerifyClient({ token }: { token: string }) {
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    const verifyAccount = async () => {
      try {
        const res = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/verify`,
          {
            params: { token },
          },
        );

        setStatus("success");
        setMessage(res.data.message || "Account Verified Successfully!!");
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

    verifyAccount();
  }, [token]);

  if (!token) {
    setStatus("error");
    setMessage("No verification token provided.");
  }

  return (
    <div className="flex flex-col items-center space-y-6 text-center">
      <h2 className="text-3xl font-bold text-slate-800">
        Account Verification
      </h2>

      {status === "loading" && (
        <p className="text-slate-600 animate-pulse">
          Verifying your account...
        </p>
      )}

      {status === "success" && (
        <>
          <p className="text-green-600 font-medium">{message}</p>
          <Link
            href="/signin"
            className="px-8 py-4 w-full rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] transition-all duration-300"
          >
            Continue to Sign In
          </Link>
        </>
      )}

      {status === "error" && (
        <p className="text-red-500 font-medium">{message}</p>
      )}
    </div>
  );
}
