import { useEffect, useState } from "react";
import { apiCall } from "../lib/api";

export const Verify = () => {
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const verifyToken = async () => {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token");

      if (!token) {
        setStatus("error");
        setErrorMessage("Verification token is missing from the URL.");
        return;
      }

      try {
        await apiCall(`/auth/verify?token=${token}`, {}, "GET");

        setStatus("success");
      } catch (error: any) {
        const status = error?.status;

        if (status === 403) {
          setStatus("error");
          setErrorMessage(
            error?.message ||
              "The verification link is invalid or has expired.",
          );
        } else {
          setStatus("error");
          setErrorMessage("Verification failed.");
        }
      }
    };

    verifyToken();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-sm border border-slate-200 text-center">
        {status === "loading" && (
          <div className="animate-pulse">
            <div className="h-12 w-12 bg-slate-200 rounded-full mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-slate-900">
              Verifying your account...
            </h2>
          </div>
        )}

        {status === "success" && (
          <div>
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 mb-4">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4.5 12.75l6 6 9-13.5"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Account Verified Successfully!
            </h2>
            <p className="text-slate-500 mb-6">
              Your email has been verified. You can now access your dashboard.
            </p>
            <a
              href="/signin"
              className="inline-flex justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
            >
              Continue to Sign In
            </a>
          </div>
        )}

        {status === "error" && (
          <div>
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 mb-4">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              Verification Failed
            </h2>
            <p className="text-slate-500 mb-6">{errorMessage}</p>
            <a
              href="/signin"
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-500"
            >
              Back to Sign In
            </a>
          </div>
        )}
      </div>
    </div>
  );
};
