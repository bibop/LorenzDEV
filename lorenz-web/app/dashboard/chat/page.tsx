'use client';

import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Message as MessageType } from '@/types';
import { Send, Sparkles, Database, Brain, Zap, Mic, MicOff } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useSimulatedAudio } from '@/components/voice';
import type { OrbState } from '@/components/voice';
import {
  Message,
  MessageContent,
  MessageAvatar,
  MessageMetadata,
  MessageBadge,
} from '@/components/ui/message';
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
  ConversationTyping,
} from '@/components/ui/conversation';
import { Response } from '@/components/ui/response';
import { VoiceButton } from '@/components/ui/voice-button';
import { ShimmeringText } from '@/components/ui/shimmering-text';

// Dynamically import VoiceOrb to avoid SSR issues with Three.js
const VoiceOrb = dynamic(() => import('@/components/voice/VoiceOrb'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full rounded-full bg-gradient-to-br from-primary/30 to-secondary/30 animate-pulse" />
  )
});

export default function ChatPage() {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [orbState, setOrbState] = useState<OrbState>('idle');
  const inputRef = useRef<HTMLInputElement>(null);

  // Simulated audio for demo (can be replaced with real audio)
  const { inputVolume, outputVolume, startSimulation, stopSimulation } = useSimulatedAudio();

  // Pastel colors for the orb
  const orbColors = {
    primary: '#C4B5FD',    // Soft lavender
    secondary: '#93C5FD',  // Soft blue
    glow: '#A5B4FC'        // Light indigo
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: MessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setOrbState('thinking');
    startSimulation('output');

    try {
      const response = await api.sendMessage(userMessage.content);

      const assistantMessage: MessageType = {
        id: response.message_id || response.id || Date.now().toString(),
        role: 'assistant',
        content: response.content || response.response || response.message || 'Mi dispiace, non ho una risposta.',
        created_at: new Date().toISOString(),
        metadata: {
          model: response.model,
          skill_used: response.skill_used,
          twin_processed: response.twin_processed,
          rag_context_used: response.rag_context_used,
          mneme_context_used: response.mneme_context_used,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: MessageType = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Mi dispiace, si è verificato un errore. Riprova più tardi.',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setOrbState('speaking');
      setTimeout(() => {
        stopSimulation();
        setOrbState('idle');
      }, 2000);
    }
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    inputRef.current?.focus();
  };

  const quickActions = [
    { label: 'Controlla email', action: 'Controlla le mie email', color: 'lavender' },
    { label: 'Genera immagine', action: "Genera un'immagine di ", color: 'blue' },
    { label: 'Cerca nel web', action: 'Cerca informazioni su ', color: 'mint' },
    { label: 'Riassumi', action: 'Riassumi questo documento: ', color: 'peach' },
  ] as const;

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Minimal Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10">
            <VoiceOrb
              state={orbState}
              inputVolume={inputVolume}
              outputVolume={outputVolume}
              colors={orbColors}
              size={0.7}
              className="w-full h-full"
            />
          </div>
          <div>
            <h1 className="text-lg font-medium text-foreground">Lorenz</h1>
            <p className="text-xs text-muted-foreground">Il tuo assistente personale</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="chip chip-mint">
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            Online
          </span>
        </div>
      </div>

      {/* Chat Area */}
      <Conversation className="flex-1">
        <ConversationContent>
          {messages.length === 0 ? (
            <ConversationEmptyState
              title=""
              description=""
            >
              <div className="flex flex-col items-center justify-center py-12">
                {/* Large Orb */}
                <div className="w-48 h-48 mb-8">
                  <VoiceOrb
                    state={orbState}
                    inputVolume={inputVolume}
                    outputVolume={outputVolume}
                    colors={orbColors}
                    size={1.2}
                    className="w-full h-full"
                  />
                </div>

                {/* Welcome text */}
                <ShimmeringText
                  text="Ciao! Sono Lorenz"
                  className="text-2xl font-medium mb-3"
                  shimmerColor="hsl(252 85% 78%)"
                  duration={3}
                />
                <p className="text-muted-foreground text-center max-w-md mb-8">
                  Il tuo assistente personale AI. Posso aiutarti con email, ricerche,
                  generazione di contenuti e molto altro.
                </p>

                {/* Quick Actions */}
                <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                  {quickActions.map((qa) => (
                    <button
                      key={qa.label}
                      onClick={() => handleQuickAction(qa.action)}
                      className={`chip chip-${qa.color} cursor-pointer hover:scale-105 transition-smooth px-4 py-2`}
                    >
                      {qa.label}
                    </button>
                  ))}
                </div>
              </div>
            </ConversationEmptyState>
          ) : (
            <>
              {messages.map((message) => (
                <Message key={message.id} from={message.role === 'user' ? 'user' : 'assistant'}>
                  <MessageAvatar
                    name={message.role === 'user' ? 'Tu' : 'Lo'}
                  />
                  <MessageContent variant={message.role === 'assistant' ? 'flat' : 'contained'}>
                    {message.role === 'assistant' ? (
                      <Response>{message.content}</Response>
                    ) : (
                      <p className="text-foreground">{message.content}</p>
                    )}

                    {/* Metadata badges */}
                    {message.role === 'assistant' && (
                      message.metadata?.twin_processed ||
                      message.metadata?.rag_context_used ||
                      message.metadata?.mneme_context_used ||
                      message.metadata?.skill_used
                    ) && (
                      <MessageMetadata>
                        {message.metadata?.twin_processed && (
                          <MessageBadge variant="lavender" icon={<Zap />}>
                            Twin
                          </MessageBadge>
                        )}
                        {message.metadata?.rag_context_used && (
                          <MessageBadge variant="blue" icon={<Database />}>
                            RAG
                          </MessageBadge>
                        )}
                        {message.metadata?.mneme_context_used && (
                          <MessageBadge variant="mint" icon={<Brain />}>
                            MNEME
                          </MessageBadge>
                        )}
                        {message.metadata?.skill_used && (
                          <MessageBadge variant="peach" icon={<Sparkles />}>
                            {message.metadata.skill_used}
                          </MessageBadge>
                        )}
                      </MessageMetadata>
                    )}
                  </MessageContent>
                </Message>
              ))}

              {/* Loading state */}
              {isLoading && (
                <Message from="assistant">
                  <div className="w-9 h-9">
                    <VoiceOrb
                      state="thinking"
                      outputVolume={outputVolume}
                      colors={orbColors}
                      size={0.6}
                      className="w-full h-full"
                    />
                  </div>
                  <MessageContent variant="flat">
                    <ConversationTyping name="Lorenz" />
                  </MessageContent>
                </Message>
              )}
            </>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {/* Input Area */}
      <div className="p-4 border-t border-border/50 bg-background">
        <form onSubmit={handleSubmit} className="flex items-center gap-3 max-w-3xl mx-auto">
          <VoiceButton
            variant="pastel"
            size="icon"
            state="idle"
            className="shrink-0"
          />
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Scrivi un messaggio..."
            className="input-minimal flex-1"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="shrink-0 w-10 h-10 rounded-xl bg-primary/15 text-primary
                     hover:bg-primary/25 transition-smooth
                     disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center justify-center"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <p className="text-xs text-muted-foreground/50 text-center mt-2">
          Lorenz può commettere errori. Verifica le informazioni importanti.
        </p>
      </div>
    </div>
  );
}
