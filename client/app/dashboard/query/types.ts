export  interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    isStreaming?: boolean;
}

export interface Source {
    source_number: string;
    file_name: string;
    page_number: string;
    access_url: string;
}