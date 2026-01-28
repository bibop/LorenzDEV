'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Message } from '@/components/chat/message';
import { ChatInput } from '@/components/chat/chat-input';
import { ConversationList } from '@/components/chat/conversation-list';
import { VoiceSettings } from '@/components/voice/voice-settings';
import { PersonaEditor } from '@/components/voice/persona-editor';
import { VoiceUploader } from '@/components/voice/voice-uploader';
import { VoiceChat } from '@/components/voice/voice-chat';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { ErrorBoundary } from '@/components/error-boundary';

interface ChatMessage {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
}

interface Conversation {
    id: string;
    title: string;
    lastMessage?: string;
    updatedAt: Date;
}

export default function ChatPage() {
    const router = useRouter();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeConversationId, setActiveConversationId] = useState<string>();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showVoiceSettings, setShowVoiceSettings] = useState(false);
    const [showPersonaEditor, setShowPersonaEditor] = useState(false);
    const [showVoiceUploader, setShowVoiceUploader] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState<'personaplex' | 'elevenlabs'>('elevenlabs');
    const [selectedVoice, setSelectedVoice] = useState('');
    const [isVoiceChatActive, setIsVoiceChatActive] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Check authentication
        if (!api.isAuthenticated()) {
            router.push('/login');
            return;
        }

        // Load conversations (mock data for now)
        setConversations([
            {
                id: '1',
                title: 'Getting started with LORENZ',
                lastMessage: 'How can I help you today?',
                updatedAt: new Date(),
            },
        ]);

        // Load first conversation by default
        if (conversations.length > 0 && !activeConversationId) {
            setActiveConversationId(conversations[0].id);
            loadConversation(conversations[0].id);
        }
    }, [router, conversations.length, activeConversationId]);

    const loadConversation = async (conversationId: string) => {
        // Mock messages for now
        setMessages([
            {
                id: '1',
                content: 'Hello! How can I help you today?',
                role: 'assistant',
                timestamp: new Date(Date.now() - 60000),
            },
        ]);
    };

    const handleSendMessage = async (content: string) => {
        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            content,
            role: 'user',
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // TODO: Replace with actual API call
            // const response = await api.sendChatMessage(activeConversationId, content);

            // Mock AI response
            setTimeout(() => {
                const aiMessage: ChatMessage = {
                    id: (Date.now() + 1).toString(),
                    content: "I'm a demo response. The real AI integration is coming soon!",
                    role: 'assistant',
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, aiMessage]);
                setIsLoading(false);
            }, 1000);
        } catch (error) {
            console.error('Failed to send message:', error);
            setIsLoading(false);
        }
    };

    const handleNewConversation = () => {
        const newConv: Conversation = {
            id: Date.now().toString(),
            title: 'New Conversation',
            updatedAt: new Date(),
        };
        setConversations((prev) => [newConv, ...prev]);
        setActiveConversationId(newConv.id);
        setMessages([]);
    };

    const handleLogout = () => {
        api.logout();
        router.push('/login');
    };

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <div
                className={cn(
                    "border-r bg-muted/30 transition-all duration-300",
                    sidebarOpen ? "w-64" : "w-0 overflow-hidden"
                )}
            >
                <ConversationList
                    conversations={conversations}
                    activeConversationId={activeConversationId}
                    onSelect={(id) => {
                        setActiveConversationId(id);
                        loadConversation(id);
                    }}
                    onNew={handleNewConversation}
                />
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <div className="flex items-center justify-between px-4 py-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => setSidebarOpen(!sidebarOpen)}
                                >
                                    {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                                </Button>
                                <h1 className="text-xl font-semibold">LORENZ Chat</h1>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant={showVoiceSettings ? "default" : "ghost"}
                                    size="icon"
                                    onClick={() => setShowVoiceSettings(!showVoiceSettings)}
                                    title="Voice Settings"
                                >
                                    <Mic className="h-5 w-5" />
                                </Button>
                                <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard')}>
                                    <Settings className="h-5 w-5" />
                                </Button>
                                <Button variant="ghost" size="icon" onClick={handleLogout}>
                                    <LogOut className="h-5 w-5" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Voice Chat Section */}


                {/* Messages */}
                <ScrollArea className="flex-1 p-4">
                    <div className="max-w-3xl mx-auto">
                        {messages.length === 0 ? (
                            <div className="flex h-full items-center justify-center">
                                <div className="text-center space-y-4">
                                    <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2">
                                        <Mic className="h-4 w-4 text-primary" />
                                        <span className="text-sm font-medium text-primary">Start a new conversation</span>
                                    </div>
                                    <p className="text-muted-foreground">
                                        Ask me anything about your documents, tasks, or skills
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <>
                                {messages.map((message) => (
                                    <Message
                                        key={message.id}
                                        content={message.content}
                                        isUser={message.role === 'user'}
                                        timestamp={message.timestamp}
                                    />
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start mb-4">
                                        <div className="bg-muted rounded-lg px-4 py-3">
                                            <div className="flex gap-1">
                                                <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" />
                                                <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce [animation-delay:0.2s]" />
                                                <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce [animation-delay:0.4s]" />
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>
                </ScrollArea>

                {/* Input Area */}
                <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4">
                    <div className="max-w-3xl mx-auto space-y-4">
                        {/* Voice Mode Toggle */}
                        {isVoiceChatActive && (
                            <Card className="p-4 border-primary/20 bg-primary/5">
                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-sm font-medium flex items-center gap-2">
                                        <Mic className="h-4 w-4 text-primary" />
                                        Voice Mode Active
                                    </span>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setIsVoiceChatActive(false)}
                                        className="h-8 w-8 p-0"
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>
                                <VoiceChat
                                    conversationId={activeConversationId || ''}
                                    provider={selectedProvider}
                                    voiceId={selectedVoice}
                                    onTranscript={(text, isUser) => {
                                        const newMessage: ChatMessage = {
                                            id: Date.now().toString(),
                                            content: text,
                                            role: isUser ? 'user' : 'assistant',
                                            timestamp: new Date(),
                                        };
                                        setMessages((prev) => [...prev, newMessage]);
                                    }}
                                />
                            </Card>
                        )}

                        {!isVoiceChatActive && (
                            <ChatInput
                                onSend={handleSendMessage}
                                disabled={isLoading}
                                onVoiceClick={() => setIsVoiceChatActive(true)}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* Voice Settings Panel */}
            {showVoiceSettings && (
                <ErrorBoundary
                    fallback={
                        <div className="fixed right-0 top-0 h-screen w-96 bg-background border-l shadow-lg z-50 p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Voice Settings</h2>
                                <Button variant="ghost" size="icon" onClick={() => setShowVoiceSettings(false)}>
                                    <X className="h-5 w-5" />
                                </Button>
                            </div>
                            <div className="text-muted-foreground">
                                Loading voice settings encountered an error. Please refresh the page.
                            </div>
                        </div>
                    }
                >
                    <div className="fixed right-0 top-0 h-screen w-96 bg-background border-l shadow-lg z-50 overflow-y-auto">
                        <div className="p-4 border-b flex items-center justify-between">
                            <h2 className="text-lg font-semibold flex items-center gap-2">
                                <Mic className="h-5 w-5 text-primary" />
                                Voice Settings
                            </h2>
                            <Button variant="ghost" size="icon" onClick={() => setShowVoiceSettings(false)}>
                                <X className="h-5 w-5" />
                            </Button>
                        </div>
                        <div className="p-4 space-y-4">
                            <VoiceSettings
                                selectedProvider={selectedProvider}
                                selectedVoice={selectedVoice}
                                onProviderChange={(provider) => setSelectedProvider(provider as 'personaplex' | 'elevenlabs')}
                                onVoiceChange={setSelectedVoice}
                            />
                            <div className="space-y-2">
                                <Button
                                    className="w-full"
                                    variant="outline"
                                    onClick={() => setShowPersonaEditor(true)}
                                >
                                    <Plus className="mr-2 h-4 w-4" />
                                    Create Persona
                                </Button>
                                <Button
                                    className="w-full"
                                    variant="outline"
                                    onClick={() => setShowVoiceUploader(true)}
                                >
                                    <Upload className="mr-2 h-4 w-4" />
                                    Upload Voice
                                </Button>
                            </div>
                        </div>
                    </div>
                </ErrorBoundary>
            )}

            {/* Modals */}
            <PersonaEditor
                open={showPersonaEditor}
                onOpenChange={setShowPersonaEditor}
                onSuccess={() => {
                    // Refresh personas list
                }}
            />
            <VoiceUploader
                open={showVoiceUploader}
                onOpenChange={setShowVoiceUploader}
                onSuccess={() => {
                    // Refresh voices list
                }}
            />
        </div>
    );
}
