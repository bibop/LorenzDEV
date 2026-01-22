"use client";

import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStickToBottom } from "use-stick-to-bottom"; // Checking package.json earlier, this was present. If not, will fallback.

// Fallback if use-stick-to-bottom is complex to setup without config, 
// but assuming package.json had it, we will try standard scrollIntoView first for simplicity/robustness.

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
}

interface MessageListProps {
    messages: Message[];
    isThinking?: boolean;
}

export function MessageList({ messages, isThinking }: MessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isThinking]);

    return (
        <div className="flex-1 overflow-y-auto px-4 py-6 scroll-smooth">
            <div className="w-full max-w-4xl mx-auto flex flex-col justify-end min-h-full">

                {/* Welcome / Empty State */}
                {messages.length === 0 && (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 opacity-0 animate-fade-in" style={{ animationDelay: '0.2s', animationFillMode: 'forwards' }}>
                        <div className="h-16 w-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 animate-pulse-glow">
                            <span className="text-3xl">✨</span>
                        </div>
                        <h2 className="text-2xl font-semibold mb-2">How can I help you today?</h2>
                        <p className="text-muted-foreground max-w-md">
                            I can help you manage your emails, schedule meetings, or answer questions about your projects.
                        </p>
                    </div>
                )}

                {messages.map((msg) => (
                    <MessageBubble
                        key={msg.id}
                        role={msg.role}
                        content={msg.content}
                        timestamp={msg.timestamp}
                    />
                ))}

                {isThinking && (
                    <div className="flex w-full mb-6 justify-start animate-fade-in">
                        <div className="flex max-w-[80%] gap-4">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted border border-border">
                                <span className="loading-dots text-xs text-muted-foreground font-bold pl-1 tracking-widest" />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={bottomRef} className="h-4" />
            </div>
        </div>
    );
}
