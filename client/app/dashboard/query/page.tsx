"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";
import axios from "axios";
import toast from "react-hot-toast";
import { useSearchParams } from "next/navigation";

interface Source {
    source_number: string;
    file_name: string;
    page_number: string;
    access_url: string;
}

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    isStreaming?: boolean;
}

function QueryPageContent() {
    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState("");
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const searchParams = useSearchParams();

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const openDocumentFile = async (file_url: string) => {
        try {
            const res = await axios.get(file_url, {
                responseType: "blob",
                withCredentials: true,
            });
            const blob = new Blob([res.data], { type: "application/pdf" });
            const url = URL.createObjectURL(blob);
            const newTab = window.open();
            if (newTab) newTab.location = url;
        } catch {
            toast.error("Error while opening file");
        }
    };

    const handleQuerySubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || isStreaming) return;

        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: query,
        };

        const assistantMessageId = crypto.randomUUID();
        const assistantMessage: Message = {
            id: assistantMessageId,
            role: "assistant",
            content: "",
            sources: [],
            isStreaming: true,
        };

        setMessages((prev) => [...prev, userMessage, assistantMessage]);
        setQuery("");
        setError("");
        setIsStreaming(true);

        const req_body: { query: string; doc_id?: string } = {
            query: query,
        };

        if (searchParams.get("document") != null) {
            req_body.doc_id = searchParams.get("document") as string;
        }

        try {
            const res = await fetch(
                process.env.NEXT_PUBLIC_API_URL + "/query/ask",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(req_body),
                    credentials: "include",
                }
            );

            if (!res.ok) throw new Error("Failed to process query");

            const reader = res.body?.getReader();
            const decoder = new TextDecoder();
            if (!reader) throw new Error("Streaming not supported");

            let fullResponse = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                fullResponse += decoder.decode(value, { stream: true });

                const answerPart = fullResponse.split("<SOURCES>")[0];

                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.id === assistantMessageId
                            ? { ...msg, content: answerPart }
                            : msg
                    )
                );
            }

            const sourcesPart = fullResponse.split("<SOURCES>")[1];
            let parsedSources: Source[] = [];
            if (sourcesPart) {
                const cleaned = sourcesPart.slice(0, -10).trim();
                try {
                    parsedSources = JSON.parse(cleaned);
                } catch {
                    console.error("Failed to parse sources", cleaned);
                }
            }

            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === assistantMessageId
                        ? { ...msg, isStreaming: false, sources: parsedSources }
                        : msg
                )
            );
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.error || "Failed to process request");
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("An unexpected error occurred");
            }

            setMessages((prev) =>
                prev.filter((msg) => msg.id !== assistantMessageId)
            );
        } finally {
            setIsStreaming(false);
        }
    };

    const clearHistory = () => {
        setMessages([]);
        setError("");
    };

    return (
        <div className="flex flex-col h-[calc(100vh-140px)] space-y-6">

            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-slate-800 tracking-tight">
                    Global Research Query
                </h2>
                <div className="flex gap-3">
                    {messages.length > 0 && (
                        <button
                            onClick={clearHistory}
                            className="px-4 py-2 rounded-xl font-bold text-slate-500 bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] transition-all duration-300 text-sm"
                        >
                            Clear chat
                        </button>
                    )}
                    <Link
                        href="/dashboard"
                        className="px-6 py-2 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] transition-all duration-300"
                    >
                        &larr; Back to Library
                    </Link>
                </div>
            </div>

            <p className="text-slate-600">
                Ask a question across all your embedded documents. Citations will be automatically generated.
            </p>

            {/* Chat container */}
            <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-8 rounded-4xl bg-slate-200 shadow-[inset_8px_8px_16px_#c1c9d2,inset_-8px_-8px_16px_#ffffff] relative space-y-6"
            >
                {error && (
                    <div className="text-red-500 font-medium mb-4 text-center">{error}</div>
                )}

                {messages.length === 0 && !error && (
                    <div className="h-full flex items-center justify-center text-slate-400 font-medium text-lg">
                        Your insights will appear here...
                    </div>
                )}

                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        {msg.role === "user" ? (
                            /* ── User bubble ── */
                            <div className="max-w-[75%] px-5 py-3 rounded-3xl rounded-br-sm bg-blue-600 text-white text-sm leading-relaxed shadow-md">
                                {msg.content}
                            </div>
                        ) : (
                            /* ── Assistant bubble ── */
                            <div className="w-full">
                                <div className="prose prose-slate max-w-none prose-headings:text-slate-800 prose-a:text-blue-600 prose-strong:text-slate-700 prose-code:text-slate-800 prose-code:bg-slate-300 prose-code:px-1 prose-code:rounded prose-blockquote:border-l-blue-500 prose-blockquote:text-slate-600 prose-blockquote:italic">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>

                                    {/* streaming cursor */}
                                    {msg.isStreaming && (
                                        <span className="inline-block w-2 h-5 bg-slate-500 animate-pulse ml-1 align-middle" />
                                    )}
                                </div>

                                {/* Sources — only shown after streaming completes */}
                                {!msg.isStreaming && msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-6 border-t border-slate-300 pt-4">
                                        <h3 className="text-sm font-semibold text-slate-600 mb-3">
                                            Sources
                                        </h3>
                                        <div className="grid gap-2">
                                            {msg.sources.map((source) => (
                                                <button
                                                    key={`${source.source_number}-${source.page_number}`}
                                                    onClick={() => openDocumentFile(source.access_url)}
                                                    className="text-left p-3 rounded-2xl bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] transition-all duration-200"
                                                >
                                                    <div className="flex items-start gap-3">
                                                        <span className="text-lg">📄</span>
                                                        <div className="flex-1">
                                                            <div className="font-medium text-slate-800 text-sm break-words">
                                                                {source.file_name}
                                                            </div>
                                                            <div className="mt-0.5 text-xs text-slate-500">
                                                                Source {source.source_number} • Page {source.page_number}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Input */}
            <form
                onSubmit={handleQuerySubmit}
                className="flex gap-4 p-4 rounded-3xl bg-slate-200 shadow-[12px_12px_24px_#c1c9d2,-12px_-12px_24px_#ffffff]"
            >
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., What are the main findings regarding quantum entanglement?"
                    disabled={isStreaming}
                    className="flex-1 p-4 rounded-2xl bg-slate-200 shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] focus:outline-none text-slate-700 placeholder-slate-400 disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={!query.trim() || isStreaming}
                    className="px-8 rounded-2xl font-bold text-blue-600 bg-slate-200 shadow-[6px_6px_12px_#c1c9d2,-6px_-6px_12px_#ffffff] hover:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] active:shadow-[inset_6px_6px_12px_#c1c9d2,inset_-6px_-6px_12px_#ffffff] transition-all duration-300 disabled:opacity-50 disabled:shadow-[inset_4px_4px_8px_#c1c9d2,inset_-4px_-4px_8px_#ffffff] disabled:cursor-not-allowed"
                >
                    {isStreaming ? "Thinking..." : "Send Query"}
                </button>
            </form>
        </div>
    );
}

export default function QueryPage() {
    return (
        <Suspense fallback={<div className="text-center">Loading search...</div>}>
            <QueryPageContent />
        </Suspense>
    );
}