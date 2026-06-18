'use client';

import { usePathname, useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { Message } from "./types";
import { api } from "@/app/lib/api";
import axios from "axios";

interface SidebarProps {
    sidebarOpen: boolean,
    setMessages: Dispatch<SetStateAction<Message[]>>,
    setError: Dispatch<SetStateAction<string>>
}

interface Conversation {
    id: string;
    name: string;
}

const Sidebar = ({ sidebarOpen, setMessages, setError }: SidebarProps) => {

    const [conversations, setConversations] = useState<Conversation[]>([])
    const searchParams = useSearchParams()
    const pathName = usePathname()
    const router = useRouter();
    const handleConversationClick = (conv: Conversation) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set("conversation_id", conv.id);
        router.push(`${pathName}?${params.toString()}`);
        setMessages([]);
        setError("")
    };
    const handleNewConversation = () => {
        const params = new URLSearchParams(searchParams.toString());
        params.delete("conversation_id");
        router.push(`${pathName}?${params.toString()}`);
        setMessages([]);
        setError("")
    };
    const activeConvId = searchParams.get("conversation_id")

    const getAllConversations = async () => {
        try {
            const res = await api.get(`/conversation/`);
            setConversations(res.data.conversations)
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.error || "Failed to process request");
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("An unexpected error occurred");
            }
        }
    }

    useEffect(() => {
        (async () => await getAllConversations())();
    }, [])

    return (
        <aside
            className={`shrink-0 flex flex-col gap-1 overflow-y-auto transition-all duration-300
        ${sidebarOpen ? "w-64 pr-4" : "w-0 overflow-hidden"}
    `}
        >
            {sidebarOpen && (
                <>
                    <button
                        onClick={handleNewConversation}
                        className="flex cursor-pointer items-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-bold text-blue-600 bg-slate-200 shadow-[4px_4px_8px_#c1c9d2,-4px_-4px_8px_#ffffff] hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff] transition-all duration-200 mb-2"
                    >
                        <span className="text-lg leading-none">+</span>
                        New conversation
                    </button>

                    {conversations &&
                        conversations.length > 0 &&
                        conversations.map((conv: Conversation) => {
                            const isActive = activeConvId === conv.id;

                            return (
                                <button
                                    key={conv.id}
                                    onClick={() => handleConversationClick(conv)}
                                    className={`
                    flex items-start cursor-pointer gap-2.5 w-full text-left 
                    px-3 py-2.5 rounded-xl mb-1 transition-all duration-200

                    ${isActive
                                            ? "bg-slate-200 shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff]"
                                            : "hover:bg-slate-200 hover:shadow-[inset_2px_2px_4px_#c1c9d2,inset_-2px_-2px_4px_#ffffff]"
                                        }
                `}
                                >
                                    <span
                                        className={`mt-0.5 text-sm ${isActive ? "text-blue-600" : "text-slate-400"
                                            }`}
                                    >
                                        💬
                                    </span>

                                    <div className="flex-1 min-w-0">
                                        <p
                                            className={`
                            text-sm truncate
                            ${isActive
                                                    ? "text-blue-700 font-bold"
                                                    : "text-slate-700 font-medium"
                                                }
                        `}
                                        >
                                            {conv.name}
                                        </p>
                                    </div>
                                </button>
                            );
                        })}
                </>
            )}
        </aside>
    )
}

export default Sidebar