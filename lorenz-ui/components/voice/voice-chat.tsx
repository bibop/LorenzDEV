'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { AudioStreamManager, AudioPlayer } from '@/lib/audio-stream';
import { getVoiceClient, VoiceConnectionConfig } from '@/lib/voice-websocket';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface VoiceChatProps {
    conversationId: string;
    provider: 'personaplex' | 'elevenlabs';
    voiceId: string;
    personaId?: string;
    onTranscript?: (text: string, isUser: boolean) => void;
}

export function VoiceChat({
    conversationId,
    provider,
    voiceId,
    personaId,
    onTranscript,
}: VoiceChatProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [error, setError] = useState('');

    const audioManager = useRef<AudioStreamManager | null>(null);
    const audioPlayer = useRef<AudioPlayer | null>(null);
    const voiceClient = useRef(getVoiceClient());

    useEffect(() => {
        // Initialize audio player
        audioPlayer.current = new AudioPlayer();
        audioPlayer.current.initialize();

        return () => {
            cleanup();
        };
    }, []);

    const startVoiceChat = async () => {
        setError('');
        setIsConnecting(true);

        try {
            // Connect WebSocket
            const config: VoiceConnectionConfig = {
                conversationId,
                provider,
                voiceId,
                personaId,
                token: api.getToken() || '',
            };

            await voiceClient.current.connect(config);
            setIsConnected(true);

            // Set up message handlers
            voiceClient.current.onAudio((audioData) => {
                setIsSpeaking(true);
                audioPlayer.current?.playChunk(audioData);
                setTimeout(() => setIsSpeaking(false), 100);
            });

            voiceClient.current.onTranscript((text) => {
                onTranscript?.(text, false);
            });

            voiceClient.current.onError((errMsg) => {
                setError(errMsg);
            });

            // Start audio capture
            audioManager.current = new AudioStreamManager();
            await audioManager.current.startCapture({
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            });

            // Stream audio chunks to server
            audioManager.current.onChunk((chunk) => {
                if (voiceClient.current.isConnected()) {
                    voiceClient.current.sendAudio(chunk);
                }
            });

            setIsRecording(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start voice chat');
            cleanup();
        } finally {
            setIsConnecting(false);
        }
    };

    const stopVoiceChat = () => {
        cleanup();
    };

    const toggleMute = () => {
        if (isRecording) {
            audioManager.current?.stopCapture();
            setIsRecording(false);
        } else if (isConnected) {
            audioManager.current?.startCapture();
            setIsRecording(true);
        }
    };

    const cleanup = () => {
        audioManager.current?.stopCapture();
        audioPlayer.current?.stop();
        voiceClient.current.disconnect();
        setIsRecording(false);
        setIsConnected(false);
        setIsSpeaking(false);
    };

    return (
        <div className="space-y-4">
            {error && (
                <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                    {error}
                </div>
            )}

            <div className="flex items-center justify-center gap-4">
                {!isConnected ? (
                    <Button
                        size="lg"
                        onClick={startVoiceChat}
                        disabled={isConnecting}
                        className="gap-2"
                    >
                        {isConnecting ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                Connecting...
                            </>
                        ) : (
                            <>
                                <Mic className="h-5 w-5" />
                                Start Voice Chat
                            </>
                        )}
                    </Button>
                ) : (
                    <>
                        <Button
                            size="lg"
                            variant={isRecording ? 'default' : 'secondary'}
                            onClick={toggleMute}
                            className={cn(
                                'gap-2',
                                isRecording && 'animate-pulse bg-primary'
                            )}
                        >
                            {isRecording ? (
                                <>
                                    <Mic className="h-5 w-5" />
                                    Listening...
                                </>
                            ) : (
                                <>
                                    <MicOff className="h-5 w-5" />
                                    Muted
                                </>
                            )}
                        </Button>

                        <div className="flex items-center gap-2">
                            {isSpeaking ? (
                                <Volume2 className="h-5 w-5 text-primary animate-pulse" />
                            ) : (
                                <VolumeX className="h-5 w-5 text-muted-foreground" />
                            )}
                            <span className="text-sm text-muted-foreground">
                                {isSpeaking ? 'AI Speaking...' : 'Waiting...'}
                            </span>
                        </div>

                        <Button size="lg" variant="destructive" onClick={stopVoiceChat}>
                            End Chat
                        </Button>
                    </>
                )}
            </div>

            {/* Visual indicator */}
            {isRecording && (
                <div className="flex justify-center">
                    <div className="flex gap-1">
                        {[...Array(5)].map((_, i) => (
                            <div
                                key={i}
                                className="h-8 w-2 bg-primary rounded-full animate-pulse"
                                style={{
                                    animationDelay: `${i * 0.1}s`,
                                    animationDuration: '1s',
                                }}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
