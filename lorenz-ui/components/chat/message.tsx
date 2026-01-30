import { useState } from 'react';
import { cn } from '@/lib/utils';
import { User, Bot, Volume2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface MessageProps {
    content: string;
    isUser: boolean;
    timestamp: Date;
    onSpeak?: () => Promise<void>;
}

export function Message({ content, isUser, timestamp, onSpeak }: MessageProps) {
    const [isSpeaking, setIsSpeaking] = useState(false);

    const handleSpeak = async () => {
        if (!onSpeak || isSpeaking) return;
        setIsSpeaking(true);
        try {
            await onSpeak();
        } finally {
            setIsSpeaking(false);
        }
    };

    return (
        <div
            className={cn(
                "flex w-full gap-4 mb-6",
                isUser ? "flex-row-reverse" : "flex-row"
            )}
        >
            <div
                className={cn(
                    "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow",
                    isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                )}
            >
                {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div
                className={cn(
                    "flex flex-col gap-2 max-w-[80%]",
                    isUser ? "items-end" : "items-start"
                )}
            >
                <div
                    className={cn(
                        "rounded-2xl px-4 py-2 text-sm shadow-sm",
                        isUser
                            ? "bg-primary text-primary-foreground rounded-tr-none"
                            : "bg-muted/50 backdrop-blur-sm border border-primary/10 rounded-tl-none"
                    )}
                >
                    {content}
                </div>
            </div>
        </div>
    );
}
