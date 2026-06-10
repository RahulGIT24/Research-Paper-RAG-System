"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

type DocStatus = "uploaded" | "processing" | "embedded" | "failed";

interface Document {
    id: string;
    original_file_name: string;
    server_file_name: string;
    file_ext: string;
    uploaded_at: string;
    status: DocStatus;
}

interface PaginationState {
    page: number;
    limit: number;
    total: number;
}

export default function DashboardPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [pagination, setPagination] = useState<PaginationState>({ page: 1, limit: 10, total: 0 });
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Fetch Documents
    const fetchDocuments = async (page = 1) => {
        setLoading(true);
        try {
            const res = await axios.get(process.env.NEXT_PUBLIC_API_URL + "/document/", {
                params: { page, limit: 10 },
                withCredentials: true
            });
            setDocuments(res.data.documents);
            setPagination({
                page: res.data.page,
                limit: res.data.limit,
                total: res.data.total,
            });
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.message || "Failed to load documents.");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        (
            async () => {
                await fetchDocuments();
            }
        )()

        const hasProcessingDocs = documents.some(d => d.status === "uploaded" || d.status === "processing");
        let interval: NodeJS.Timeout;

        if (hasProcessingDocs) {
            interval = setInterval(() => {
                fetchDocuments(pagination.page);
            }, 5000);
        }

        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [documents.map(d => d.status).join(",")]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (file.type !== "application/pdf") {
            setError("Only PDF files are accepted.");
            return;
        }

        setUploading(true);
        setError("");

        const formData = new FormData();
        formData.append("file", file);

        try {
            await axios.post(process.env.NEXT_PUBLIC_API_URL + "/document/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                withCredentials: true
            });

            fetchDocuments(1);

            if (fileInputRef.current) fileInputRef.current.value = "";
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.message || "Upload failed.");
            }
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm("Are you sure you want to delete this document?")) return;

        try {
            await axios.delete(process.env.NEXT_PUBLIC_API_URL + `/document/${id}`, { withCredentials: true });
            fetchDocuments(pagination.page);
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.message || "Failed to delete document.");
            }
        }
    };

    const getStatusDisplay = (status: DocStatus) => {
        switch (status) {
            case "uploaded":
                return { text: "Queued", color: "text-blue-500", dot: "bg-blue-500" };
            case "processing":
                return { text: "Processing...", color: "text-yellow-600", dot: "bg-yellow-500 animate-ping" };
            case "embedded":
                return { text: "Ingested Successfully", color: "text-green-600 font-bold", dot: "bg-green-500" };
            case "failed":
                return { text: "Ingestion Failed", color: "text-red-500", dot: "bg-red-500" };
            default:
                return { text: "Unknown", color: "text-slate-500", dot: "bg-slate-500" };
        }
    };

    const openDocumentFile = async (file_name: string) => {
        try {
            const res = await axios.get(process.env.NEXT_PUBLIC_API_URL + "/document/view/" + file_name, {
                responseType: "blob",
                withCredentials: true
            });
            const blob = new Blob([res.data], { type: "application/pdf" });
            const url = URL.createObjectURL(blob);

            const newTab = window.open();
            if (newTab) newTab.location = url;
        } catch (error) {
            toast.error("Error while opening file")
        }
    }

    const router = useRouter()

    return (
        <div className="flex flex-col space-y-10">

            {/* Upload Section */}
            <section className="p-8 rounded-4xl bg-slate-200 shadow-[12px_12px_24px_#c1c9d2,-12px_-12px_24px_#ffffff] flex flex-col items-center">
                <h2 className="text-2xl font-bold text-slate-800 mb-2">Ingest New Research</h2>
                <p className="text-slate-600 mb-6 text-sm">Upload a PDF to process and vectorise its contents.</p>

                {error && <p className="text-red-500 font-medium mb-4">{error}</p>}

                <label className={`cursor-pointer px-8 py-4 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] transition-all duration-300 ${uploading ? 'opacity-50 pointer-events-none shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff]' : 'hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff]'}`}>
                    {uploading ? "Uploading..." : "Select PDF Document"}
                    <input
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={handleFileUpload}
                        ref={fileInputRef}
                        disabled={uploading}
                    />
                </label>
            </section>

            <section className="p-8 rounded-4xl bg-slate-200 shadow-[12px_12px_24px_#c1c9d2,-12px_-12px_24px_#ffffff]">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-slate-800">Your Library</h3>
                    <span className="text-sm font-medium text-slate-500 shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] px-4 py-2 rounded-lg">
                        Total: {pagination.total}
                    </span>
                </div>

                {loading && documents.length === 0 ? (
                    <div className="text-center text-slate-500 py-10">Loading documents...</div>
                ) : documents.length === 0 ? (
                    <div className="text-center text-slate-500 py-10">No documents uploaded yet.</div>
                ) : (
                    <div className="space-y-4">
                        {documents.map((doc) => {
                            const canDelete = doc.status === "embedded" || doc.status === "failed";
                            const statusInfo = getStatusDisplay(doc.status);

                            return (
                                <div
                                    key={doc.id}
                                    className="flex items-center justify-between p-5 rounded-2xl bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff]"

                                >
                                    <div className="flex flex-col">
                                        <span className="font-semibold cursor-pointer hover:text-blue-500 text-slate-700 truncate max-w-md" onClick={() => { openDocumentFile(doc.server_file_name) }}>
                                            {doc.original_file_name}
                                        </span>
                                        <div className="flex items-center space-x-4 mt-2">
                                            <span className="text-xs font-medium text-slate-500">
                                                {new Date(doc.uploaded_at).toLocaleDateString()}
                                            </span>

                                            {/* Neumorphic Status Pill */}
                                            <div className="flex items-center space-x-2 px-3 py-1 rounded-full shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] bg-slate-200">
                                                <div className={`w-2 h-2 rounded-full ${statusInfo.dot}`}></div>
                                                <span className={`text-[10px] uppercase tracking-wider ${statusInfo.color}`}>
                                                    {statusInfo.text}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex space-x-3">
                                        {doc.status === "embedded" && (
                                            <button
                                                className="px-4 py-2 rounded-lg font-bold text-blue-600 bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] transition-all duration-300"
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    router.push(`/dashboard/query?document=${doc.id}`)
                                                }}
                                            >
                                                Query
                                            </button>
                                        )}

                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                handleDelete(doc.id)
                                            }}
                                            disabled={!canDelete}
                                            title={!canDelete ? "Document must finish processing to delete" : "Delete document"}
                                            className={`px-4 py-2 rounded-lg font-bold transition-all duration-300
                                            ${canDelete
                                                    ? "text-red-500 bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff]"
                                                    : "text-slate-400 bg-slate-200 shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] opacity-60 cursor-not-allowed"
                                                }`}
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Pagination Controls */}
                {pagination.total > pagination.limit && (
                    <div className="flex justify-center space-x-4 mt-8">
                        <button
                            disabled={pagination.page === 1}
                            onClick={() => fetchDocuments(pagination.page - 1)}
                            className="px-6 py-2 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300 disabled:opacity-50 disabled:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff]"
                        >
                            Previous
                        </button>
                        <button
                            disabled={pagination.page * pagination.limit >= pagination.total}
                            onClick={() => fetchDocuments(pagination.page + 1)}
                            className="px-6 py-2 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300 disabled:opacity-50 disabled:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff]"
                        >
                            Next
                        </button>
                    </div>
                )}
            </section>
        </div>
    );
}