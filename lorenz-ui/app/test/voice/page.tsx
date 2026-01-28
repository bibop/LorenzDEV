'use client';

import { useState } from 'react';
import { VoiceChat } from '@/components/voice/voice-chat';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function VoiceTestPage() {
    const [isActive, setIsActive] = useState(false);
    const [transcripts, setTranscripts] = useState<Array<{text: string, isUser: boolean}>>([]);

    const handleTranscript = (text: string, isUser: boolean) => {
        setTranscripts(prev => [...prev, { text, isUser }]);
    };

    return (
        <div className="container max-w-4xl mx-auto py-8 space-y-6">
            <div className="space-y-2">
                <h1 className="text-3xl font-bold">Voice Chat Test</h1>
                <p className="text-muted-foreground">
                    Test WebSocket voice streaming with ElevenLabs
                </p>
            </div>

            <Card className="p-6 space-y-6">
                <div className="space-y-2">
                    <h2 className="text-xl font-semibold">Voice Chat Controls</h2>
                    <p className="text-sm text-muted-foreground">
                        Provider: ElevenLabs | Voice: Rachel (default)
                    </p>
                </div>

                {!isActive ? (
                    <Button 
                        size="lg" 
                        onClick={() => setIsActive(true)}
                        className="w-full"
                    >
                        Start Voice Chat
                    </Button>
                ) : (
                    <div className="space-y-4">
                        <VoiceChat
                            conversationId="test-conversation"
                            provider="elevenlabs"
                            voiceId="21m00Tcm4TlvDq8ikWAM"
                            onTranscript={handleTranscript}
                        />
                        
                        <Button 
                            size="lg" 
                            variant="outline"
                            onClick={() => setIsActive(false)}
                            className="w-full"
                        >
                            Close Voice Chat
                        </Button>
                    </div>
                )}
            </Card>

            {transcripts.length > 0 && (
                <Card className="p-6 space-y-4">
                    <h2 className="text-xl font-semibold">Transcripts</h2>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {transcripts.map((t, i) => (
                            <div 
                                key={i} 
                                className={`p-3 rounded-lg ${
                                    t.isUser 
                                        ? 'bg-primary/10 ml-8' 
                                        : 'bg-muted mr-8'
                                }`}
                            >
                                <span className="text-xs font-medium text-muted-foreground">
                                    {t.isUser ? 'You' : 'AI'}
                                </span>
                                <p className="text-sm mt-1">{t.text}</p>
                            </div>
                        ))}
                    </div>
                </Card>
            )}

            <Card className="p-6 space-y-2 bg-muted/10">
                <h3 className="font-semibold">Test Instructions</h3>
                <ol className="text-sm space-y-1 list-decimal list-inside">
                    <li>Click "Start Voice Chat"</li>
                    <li>Allow microphone access when prompted</li>
                    <li>Speak into your microphone</li>
                    <li>Wait for AI voice response</li>
                    <li>Check console for WebSocket messages</li>
                </ol>
            </Card>
        </div>
    );
}
