import { cn } from "@/lib/utils";
import { MessageSquare } from "lucide-react";

interface Conversation {
    id: string;
    title: string;
    lastMessage?: string;
    updatedAt: Date;
}

interface ConversationListProps {
    conversations: Conversation[];
    activeConversationId?: string;
    onSelect: (conversationId: string) => void;
    onNew: () => void;
}

export function ConversationList({
    conversations,
    activeConversationId,
    onSelect,
    onNew,
}: ConversationListProps) {
    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b">
                <button
                    onClick={onNew}
                    className="w-full flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                    <MessageSquare className="h-4 w-4" />
                    <span className="text-sm font-medium">New Chat</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                {conversations.length === 0 ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                        No conversations yet
                    </div>
                ) : (
                    <div className="p-2 space-y-1">
                        {conversations.map((conversation) => (
                            <button
                                key={conversation.id}
                                onClick={() => onSelect(conversation.id)}
                                className={cn(
                                    "w-full text-left px-3 py-2 rounded-md transition-colors",
                                    "hover:bg-accent",
                                    activeConversationId === conversation.id
                                        ? "bg-accent"
                                        : "bg-transparent"
                                )}
                            >
                                <div className="font-medium text-sm truncate">
                                    {conversation.title}
                                </div>
                                {conversation.lastMessage && (
                                    <div className="text-xs text-muted-foreground truncate mt-1">
                                        {conversation.lastMessage}
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
