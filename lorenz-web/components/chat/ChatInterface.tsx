"use client";

import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
// import { v4 as uuidv4 } from 'uuid'; // Removed to avoid missing dependency


interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleSendMessage = async (content: string) => {
        // Add user message
        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMsg]);
        setIsLoading(true);

        // Simulate AI delay/response for UI demo
        // TODO: Connect to real backend
        setTimeout(() => {
            const aiMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: `This is a **simulated response** to: "${content}". \n\nThe UI refactor is looking great!`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, aiMsg]);
            setIsLoading(false);
        }, 1500);
    };

    return (
        <MainLayout>
            <div className="flex flex-col h-full w-full relative">
                {/* Header / Top Bar (Optional, simpler without for now) */}

                {/* Messages Area */}
                <MessageList messages={messages} isThinking={isLoading} />

                {/* Input Area */}
                <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
            </div>
        </MainLayout>
    );
}
