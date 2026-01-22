"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea"; // Assuming accessible via shadcn structure, checking later if exists
import { SendHorizontal, Paperclip, Mic, Globe } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    isLoading?: boolean;
}

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
    const [input, setInput] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = () => {
        if (input.trim() && !isLoading) {
            onSendMessage(input);
            setInput("");
            // Reset height if needed
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Simple auto-resize
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input]);

    return (
        <div className="w-full max-w-4xl mx-auto px-4 pb-6">
            <div className="relative flex items-end gap-2 bg-muted/30 border border-border/60 rounded-3xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all">

                {/* Attachment Button */}
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-10 w-10 rounded-full text-muted-foreground hover:text-foreground shrink-0 mb-0.5"
                >
                    <Paperclip className="h-5 w-5" />
                </Button>

                <div className="flex-1 min-w-0 py-2.5">
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Message Lorenz..."
                        className="w-full bg-transparent border-none focus:outline-none focus:ring-0 resize-none max-h-[200px] min-h-[24px] overflow-y-auto p-0 placeholder:text-muted-foreground/50 text-base"
                        rows={1}
                    />
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-1 shrink-0 mb-0.5">
                    {/* Voice Mode Toggle (Visual) */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-10 w-10 rounded-full text-muted-foreground hover:text-foreground"
                    >
                        <Mic className="h-5 w-5" />
                    </Button>

                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className={cn(
                            "h-10 w-10 rounded-full transition-all duration-200",
                            input.trim()
                                ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md"
                                : "bg-muted text-muted-foreground opacity-50 cursor-not-allowed"
                        )}
                    >
                        <SendHorizontal className="h-5 w-5 ml-0.5" />
                    </Button>
                </div>
            </div>
            <div className="mt-2 text-center">
                <p className="text-[10px] text-muted-foreground/40">
                    Lorenz can make mistakes. Consider checking important information.
                </p>
            </div>
        </div>
    );
}
