import { Suspense } from "react";
import ResetClient from "./ResetClient";

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const token = typeof params.token === "string" ? params.token : "";

  return (
    <Suspense fallback={<div className="text-center text-slate-600">Loading...</div>}>
      <ResetClient token={token} />
    </Suspense>
  );
}