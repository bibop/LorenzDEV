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
import { cn } from '@/lib/utils';
import { ErrorBoundary } from '@/components/error-boundary';
import { AudioPlayer } from '@/lib/audio-stream';
import { X, Menu, Mic, Settings, Bot, Plus, Upload, AudioLines, Volume2, VolumeX } from 'lucide-react';

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
    const [selectedVoice, setSelectedVoice] = useState('21m00Tcm4TlvDq8ikWAM');
    const [isVoiceChatActive, setIsVoiceChatActive] = useState(false);
    const [isAutoPlayActive, setIsAutoPlayActive] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const audioPlayerRef = useRef<AudioPlayer | null>(null);

    // Initialize AudioPlayer on mount
    useEffect(() => {
        audioPlayerRef.current = new AudioPlayer();
        audioPlayerRef.current.initialize();
        return () => {
            audioPlayerRef.current?.cleanup();
        };
    }, []);

    // Initial Load
    useEffect(() => {
        if (!api.isAuthenticated()) {
            router.push('/login');
            return;
        }

        const fetchInitialData = async () => {
            try {
                const data = await api.request<{ conversations: any[] }>('/api/v1/chat/conversations');
                if (data.conversations && data.conversations.length > 0) {
                    const formatted = data.conversations.map((c: any) => ({
                        id: c.id,
                        title: c.title || 'Untitled Conversation',
                        lastMessage: c.last_message?.content,
                        updatedAt: new Date(c.updated_at)
                    }));
                    setConversations(formatted);

                    // Auto-load most recent if none active
                    if (!activeConversationId) {
                        setActiveConversationId(formatted[0].id);
                        loadConversation(formatted[0].id);
                    }
                } else {
                    // Placeholder conversation if empty
                    setConversations([{
                        id: 'welcome',
                        title: 'Getting Started',
                        lastMessage: 'Welcome to LORENZ!',
                        updatedAt: new Date()
                    }]);
                    setMessages([{
                        id: 'system-1',
                        content: 'Welcome to LORENZ! I am your digital twin assistant. How can I help you today?',
                        role: 'assistant',
                        timestamp: new Date()
                    }]);
                    setActiveConversationId('welcome');
                }
            } catch (error) {
                console.error('Failed to load initial chat data:', error);
            }
        };

        fetchInitialData();
    }, [router]);

    const loadConversation = async (id: string) => {
        if (id === 'welcome') return;
        try {
            const data = await api.request<any[]>(`/api/v1/chat/conversations/${id}/messages`);
            setMessages(data.map((m: any) => ({
                id: m.id,
                content: m.content,
                role: m.role as 'user' | 'assistant',
                timestamp: new Date(m.created_at)
            })));
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    };

    const handleSpeakMessage = async (text: string) => {
        try {
            const audioData = await api.generateTTS(text, selectedVoice);
            await audioPlayerRef.current?.playChunk(audioData);
        } catch (error) {
            console.error('TTS playback failed:', error);
        }
    };

    const handleSendMessage = async (content: string) => {
        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            content,
            role: 'user',
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const aiMessageId = `ai-${Date.now()}`;
            let aiContent = "";

            setMessages((prev) => [...prev, {
                id: aiMessageId,
                content: "",
                role: 'assistant',
                timestamp: new Date(),
            }]);

            const convId = (activeConversationId === 'welcome') ? undefined : activeConversationId;

            for await (const chunk of api.sendChatMessageStream(convId, content)) {
                if (chunk.type === 'text') {
                    aiContent += chunk.content;
                    setMessages((prev) =>
                        prev.map(msg =>
                            msg.id === aiMessageId ? { ...msg, content: aiContent } : msg
                        )
                    );
                } else if (chunk.type === 'done') {
                    setIsLoading(false);
                    if (isAutoPlayActive) {
                        handleSpeakMessage(aiContent);
                    }
                } else if (chunk.type === 'error') {
                    console.error('Streaming error:', chunk.error);
                    setIsLoading(false);
                }
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            setIsLoading(false);
        }
    };

    const handleNewConversation = () => {
        setActiveConversationId(undefined);
        setMessages([]);
    };

    // Auto-scroll logic
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            {/* Sidebar Overlay (Mobile) */}
            {!sidebarOpen && (
                <div className="fixed inset-0 bg-black/50 z-20 md:hidden" onClick={() => setSidebarOpen(true)} />
            )}

            {/* Sidebar */}
            <aside
                className={cn(
                    "border-r bg-muted/10 backdrop-blur-xl transition-all duration-300 z-30 flex flex-col",
                    sidebarOpen ? "w-80 translate-x-0" : "w-0 -translate-x-full md:translate-x-0 md:w-0 overflow-hidden"
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
            </aside>

            {/* Main Area */}
            <main className="flex-1 flex flex-col relative min-w-0">
                {/* Header */}
                <header className="border-b bg-background/50 backdrop-blur-md z-20 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="text-muted-foreground hover:text-foreground md:hidden"
                        >
                            <Menu className="h-5 w-5" />
                        </Button>
                        {!sidebarOpen && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setSidebarOpen(true)}
                                className="text-muted-foreground hover:text-foreground hidden md:flex"
                            >
                                <Menu className="h-5 w-5" />
                            </Button>
                        )}
                        <div>
                            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400 truncate">
                                LORENZ Assistant
                            </h1>
                            <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-medium">
                                Human Digital Twin
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <Button
                            variant={isAutoPlayActive ? "default" : "ghost"}
                            size="sm"
                            onClick={() => setIsAutoPlayActive(!isAutoPlayActive)}
                            className={cn(
                                "gap-2 rounded-full px-4 h-9 border border-primary/20",
                                isAutoPlayActive ? "bg-primary text-primary-foreground" : "text-muted-foreground"
                            )}
                        >
                            {isAutoPlayActive ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                            <span className="text-xs font-semibold hidden sm:inline">Voice: {isAutoPlayActive ? "ON" : "OFF"}</span>
                        </Button>

                        <Button
                            variant={showVoiceSettings ? "secondary" : "ghost"}
                            size="icon"
                            onClick={() => setShowVoiceSettings(!showVoiceSettings)}
                            className="rounded-full h-9 w-9 border border-primary/10"
                            title="Voice Settings"
                        >
                            <AudioLines className="h-5 w-5" />
                        </Button>
                    </div>
                </header>

                {/* Messages */}
                <ScrollArea className="flex-1">
                    <div className="max-w-4xl mx-auto px-6 py-10">
                        {messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                <div className="relative group">
                                    <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full group-hover:bg-primary/30 transition-all duration-500" />
                                    <div className="relative bg-background/50 backdrop-blur-xl border border-primary/20 p-8 rounded-3xl shadow-2xl">
                                        <Bot className="h-16 w-16 text-primary animate-pulse" />
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <h2 className="text-3xl font-bold tracking-tight">Come posso aiutarti?</h2>
                                    <p className="text-muted-foreground max-w-sm mx-auto leading-relaxed">
                                        Sono il tuo Digital Twin. Posso analizzare dati, gestire compiti e interagire con te vocalmente.
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {messages.map((message) => (
                                    <Message
                                        key={message.id}
                                        content={message.content}
                                        isUser={message.role === 'user'}
                                        timestamp={message.timestamp}
                                        onSpeak={message.role === 'assistant' ? () => handleSpeakMessage(message.content) : undefined}
                                    />
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start mb-6 animate-in fade-in duration-300">
                                        <div className="bg-muted/30 backdrop-blur-sm rounded-2xl px-6 py-4 border border-primary/5 shadow-sm">
                                            <div className="flex gap-2">
                                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-duration:0.8s]" />
                                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-duration:0.8s] [animation-delay:-0.4s]" />
                                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-duration:0.8s] [animation-delay:-0.2s]" />
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} className="h-4" />
                            </div>
                        )}
                    </div>
                </ScrollArea>

                {/* Input Area */}
                <div className="p-6 bg-gradient-to-t from-background via-background to-transparent pt-10">
                    <div className="max-w-4xl mx-auto relative">
                        <ErrorBoundary
                            fallback={
                                <div className="p-4 border border-destructive/20 bg-destructive/5 rounded-2xl text-destructive text-sm text-center">
                                    Voice engine failed to initialize. Please refresh.
                                </div>
                            }
                        >
                            {isVoiceChatActive && (
                                <Card className="p-6 mb-6 border-primary/20 bg-primary/5 backdrop-blur-2xl shadow-2xl animate-in slide-in-from-bottom-4 duration-500 rounded-3xl overflow-hidden relative">
                                    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-purple-500/10 opacity-50" />
                                    <div className="relative">
                                        <div className="flex items-center justify-between mb-8">
                                            <div className="flex items-center gap-3">
                                                <div className="h-10 w-10 bg-primary/20 rounded-2xl flex items-center justify-center ring-1 ring-primary/30">
                                                    <Mic className="h-5 w-5 text-primary" />
                                                </div>
                                                <div>
                                                    <span className="text-sm font-bold block">Interazione Vocale Attiva</span>
                                                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Streaming STT / TTS</span>
                                                </div>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => setIsVoiceChatActive(false)}
                                                className="h-9 w-9 rounded-full hover:bg-destructive/10 hover:text-destructive"
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        </div>
                                        <VoiceChat
                                            conversationId={activeConversationId === 'welcome' ? 'default' : (activeConversationId || 'default')}
                                            provider={selectedProvider}
                                            voiceId={selectedVoice}
                                            onTranscript={(text, isUser) => {
                                                const newMessage: ChatMessage = {
                                                    id: `v-${Date.now()}`,
                                                    content: text,
                                                    role: isUser ? 'user' : 'assistant',
                                                    timestamp: new Date(),
                                                };
                                                setMessages((prev) => [...prev, newMessage]);
                                            }}
                                        />
                                    </div>
                                </Card>
                            )}
                        </ErrorBoundary>

                        {!isVoiceChatActive && (
                            <div className="relative group">
                                <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-500 rounded-3xl blur opacity-10 group-focus-within:opacity-20 transition duration-500" />
                                <div className="relative">
                                    <ChatInput
                                        onSend={handleSendMessage}
                                        disabled={isLoading}
                                        onVoiceClick={() => setIsVoiceChatActive(true)}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Voice Settings Panel */}
            {showVoiceSettings && (
                <div className="fixed inset-0 z-50 flex justify-end">
                    <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowVoiceSettings(false)} />
                    <aside className="relative w-[400px] bg-background/80 backdrop-blur-3xl border-l border-primary/10 shadow-2xl flex flex-col animate-in slide-in-from-right duration-500">
                        <div className="p-8 border-b border-primary/5 flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold tracking-tight">Voce & Identità</h2>
                                <p className="text-xs text-muted-foreground">Configura il tuo Digital Twin</p>
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setShowVoiceSettings(false)} className="rounded-full">
                                <X className="h-5 w-5" />
                            </Button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-8 space-y-10">
                            <VoiceSettings
                                selectedProvider={selectedProvider}
                                selectedVoice={selectedVoice}
                                onProviderChange={(provider) => setSelectedProvider(provider as 'personaplex' | 'elevenlabs')}
                                onVoiceChange={setSelectedVoice}
                            />
                            <div className="space-y-3">
                                <Button
                                    className="w-full h-12 rounded-xl"
                                    variant="outline"
                                    onClick={() => setShowPersonaEditor(true)}
                                >
                                    <Plus className="mr-2 h-4 w-4" />
                                    Personalizza Identità
                                </Button>
                                <Button
                                    className="w-full h-12 rounded-xl"
                                    variant="secondary"
                                    onClick={() => setShowVoiceUploader(true)}
                                >
                                    <Upload className="mr-2 h-4 w-4" />
                                    Clona Nuova Voce
                                </Button>
                            </div>
                        </div>
                    </aside>
                </div>
            )}

            {/* Modals */}
            <PersonaEditor
                open={showPersonaEditor}
                onOpenChange={setShowPersonaEditor}
                onSuccess={() => { }}
            />
            <VoiceUploader
                open={showVoiceUploader}
                onOpenChange={setShowVoiceUploader}
                onSuccess={() => { }}
            />
        </div>
    );
}
