"use client";

import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface MessageBubbleProps {
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
}

export function MessageBubble({ role, content, timestamp }: MessageBubbleProps) {
    const isUser = role === "user";

    return (
        <div className={cn("flex w-full mb-6", isUser ? "justify-end" : "justify-start")}>
            <div className={cn("flex max-w-[85%] md:max-w-[75%] gap-4", isUser ? "flex-row-reverse" : "flex-row")}>

                {/* Avatar */}
                <div className={cn(
                    "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full border shadow-sm",
                    isUser
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-muted text-foreground border-border"
                )}>
                    {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>

                {/* Message Content */}
                <div className={cn(
                    "flex flex-col gap-1 min-w-0"
                )}>
                    {/* Name & Time */}
                    <div className={cn(
                        "flex items-center gap-2 text-xs text-muted-foreground",
                        isUser ? "flex-row-reverse" : "flex-row"
                    )}>
                        <span className="font-medium">{isUser ? "You" : "Lorenz"}</span>
                        {timestamp && <span>{timestamp}</span>}
                    </div>

                    {/* Bubble */}
                    <div className={cn(
                        "rounded-2xl px-4 py-3 shadow-sm text-sm leading-relaxed overflow-hidden",
                        isUser
                            ? "bg-primary text-primary-foreground rounded-tr-sm"
                            : "bg-muted/50 border border-border/50 text-foreground rounded-tl-sm"
                    )}>
                        {/* Using a simple div for now, but configured for markdown content */}
                        <div className={cn("prose-lorenz", isUser && "prose-invert")}>
                            <ReactMarkdown>{content}</ReactMarkdown>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
