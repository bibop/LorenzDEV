import { cn } from "@/lib/utils";

interface MessageProps {
    content: string;
    isUser: boolean;
    timestamp?: Date;
}

export function Message({ content, isUser, timestamp }: MessageProps) {
    return (
        <div className={cn("flex w-full mb-4", isUser ? "justify-end" : "justify-start")}>
            <div
                className={cn(
                    "max-w-[80%] rounded-lg px-4 py-3 shadow-sm",
                    isUser
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground"
                )}
            >
                <div className="flex items-start gap-2">
                    {!isUser && (
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
                            AI
                        </div>
                    )}
                    <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
                        {timestamp && (
                            <p className={cn(
                                "text-xs mt-1",
                                isUser ? "text-primary-foreground/70" : "text-muted-foreground"
                            )}>
                                {timestamp.toLocaleTimeString('en-US', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
