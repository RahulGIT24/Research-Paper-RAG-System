"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";
import axios from "axios";

export default function QueryPage() {
    const [query, setQuery] = useState("");
    const [answer, setAnswer] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState("");
    const chatContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [answer]);

    const handleQuerySubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsStreaming(true);
        setError("");
        setAnswer("");

        try {
            const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/query/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query }),
                credentials: 'include'
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.message || "Failed to process query");
            }

            const reader = res.body?.getReader();
            const decoder = new TextDecoder("utf-8");

            if (!reader) throw new Error("Stream not supported by browser");

            let done = false;
            while (!done) {
                const { value, done: streamDone } = await reader.read();
                done = streamDone;
                if (value) {
                    const chunk = decoder.decode(value, { stream: true });
                    setAnswer((prev) => prev + chunk);
                }
            }
            setQuery("")
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.message || "An unexpected error occurred.");
            }
        } finally {
            setIsStreaming(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-140px)] space-y-6">

            {/* Header & Back Navigation */}
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Global Research Query</h2>
                <Link
                    href="/dashboard"
                    className="px-6 py-2 rounded-xl font-bold text-slate-700 bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] transition-all duration-300"
                >
                    &larr; Back to Library
                </Link>
            </div>

            <p className="text-slate-600">
                Ask a question across all your embedded documents. Citations will be automatically generated.
            </p>

            {/* Answer Area (Neumorphic Inset Well) */}
            <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-8 rounded-4xl bg-slate-200 shadow-[inset_8px_8px_16px_#c1c9d2,inset_-8px_-8px_16px_#ffffff] relative"
            >
                {error && (
                    <div className="text-red-500 font-medium mb-4 text-center">{error}</div>
                )}

                {!answer && !isStreaming && !error ? (
                    <div className="h-full flex items-center justify-center text-slate-400 font-medium text-lg">
                        Your insights will appear here...
                    </div>
                ) : (
                    <div className="prose prose-slate max-w-none prose-headings:text-slate-800 prose-a:text-blue-600 prose-strong:text-slate-700 prose-code:text-slate-800 prose-code:bg-slate-300 prose-code:px-1 prose-code:rounded prose-blockquote:border-l-blue-500 prose-blockquote:text-slate-600 prose-blockquote:italic">
                        {/* Render the streaming markdown */}
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {answer}
                        </ReactMarkdown>

                        {/* Blinking cursor effect while streaming */}
                        {isStreaming && (
                            <span className="inline-block w-2 h-5 bg-slate-500 animate-pulse ml-1 align-middle"></span>
                        )}
                    </div>
                )}
            </div>

            {/* Input Area */}
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