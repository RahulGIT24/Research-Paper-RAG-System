import { Suspense } from "react";
import VerifyClient from "./VerifyClient";

export default async function VerifyPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const token = typeof params.token === "string" ? params.token : "";

  return (
    <Suspense fallback={<div className="text-center text-slate-600">Loading...</div>}>
      <VerifyClient token={token} />
    </Suspense>
  );
}