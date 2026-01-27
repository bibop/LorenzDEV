'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VoiceSelector } from './voice-selector';
import { Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface VoiceProvider {
    id: string;
    name: string;
    capabilities: {
        full_duplex: boolean;
        voice_cloning: boolean;
        custom_upload: boolean;
        streaming: boolean;
        latency_ms: number;
    };
    enabled: boolean;
}

interface ProviderVoice {
    id: string;
    name: string;
    provider: string;
    category?: string;
    description?: string;
    preview_url?: string;
    labels?: Record<string, string>;
}

interface VoiceSettingsProps {
    selectedProvider?: string;
    selectedVoice?: string;
    onProviderChange: (provider: string) => void;
    onVoiceChange: (voiceId: string) => void;
}

export function VoiceSettings({
    selectedProvider,
    selectedVoice,
    onProviderChange,
    onVoiceChange,
}: VoiceSettingsProps) {
    const [providers, setProviders] = useState<VoiceProvider[]>([]);
    const [voices, setVoices] = useState<ProviderVoice[]>([]);
    const [loading, setLoading] = useState(true);
    const [playingPreview, setPlayingPreview] = useState<string | null>(null);

    useEffect(() => {
        loadProviders();
    }, []);

    useEffect(() => {
        if (selectedProvider) {
            loadProviderVoices(selectedProvider);
        }
    }, [selectedProvider]);

    const loadProviders = async () => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/voice-providers/`,
                {
                    headers: {
                        Authorization: `Bearer ${api.getToken()}`,
                    },
                }
            );
            const data = await response.json();
            setProviders(data);

            // Auto-select first enabled provider
            if (!selectedProvider && data.length > 0) {
                onProviderChange(data[0].id);
            }
        } catch (error) {
            console.error('Failed to load providers:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadProviderVoices = async (providerId: string) => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/voice-providers/${providerId}/voices`,
                {
                    headers: {
                        Authorization: `Bearer ${api.getToken()}`,
                    },
                }
            );
            const data = await response.json();
            setVoices(data);
        } catch (error) {
            console.error('Failed to load voices:', error);
        }
    };

    const playPreview = async (previewUrl: string, voiceId: string) => {
        if (playingPreview === voiceId) {
            // Stop preview
            setPlayingPreview(null);
            return;
        }

        setPlayingPreview(voiceId);
        const audio = new Audio(previewUrl);
        audio.onended = () => setPlayingPreview(null);
        audio.play();
    };

    if (loading) {
        return <div className="text-center py-8">Loading voice providers...</div>;
    }

    return (
        <div className="space-y-6">
            {/* Provider Selection */}
            <Card>
                <CardHeader>
                    <CardTitle>Voice Provider</CardTitle>
                    <CardDescription>
                        Choose between different AI voice providers
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs value={selectedProvider} onValueChange={onProviderChange}>
                        <TabsList className="grid w-full grid-cols-2">
                            {providers.map((provider) => (
                                <TabsTrigger key={provider.id} value={provider.id} disabled={!provider.enabled}>
                                    {provider.name}
                                    {!provider.enabled && (
                                        <Badge variant="outline" className="ml-2">
                                            Disabled
                                        </Badge>
                                    )}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        {providers.map((provider) => (
                            <TabsContent key={provider.id} value={provider.id} className="mt-4">
                                <div className="space-y-4">
                                    {/* Provider Capabilities */}
                                    <div className="grid grid-cols-2 gap-3 text-sm">
                                        <div className="flex items-center gap-2">
                                            {provider.capabilities.full_duplex ? (
                                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                            ) : (
                                                <AlertCircle className="h-4 w-4 text-muted-foreground" />
                                            )}
                                            <span>Full-duplex conversation</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {provider.capabilities.voice_cloning ? (
                                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                            ) : (
                                                <AlertCircle className="h-4 w-4 text-muted-foreground" />
                                            )}
                                            <span>Voice cloning</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {provider.capabilities.streaming ? (
                                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                            ) : (
                                                <AlertCircle className="h-4 w-4 text-muted-foreground" />
                                            )}
                                            <span>Streaming audio</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-muted-foreground">
                                                Latency: {provider.capabilities.latency_ms}ms
                                            </span>
                                        </div>
                                    </div>

                                    {/* Voice List for selected provider */}
                                    <div className="space-y-2">
                                        <h4 className="font-medium">Available Voices</h4>
                                        <div className="grid gap-2 max-h-96 overflow-y-auto">
                                            {voices.map((voice) => (
                                                <Card
                                                    key={voice.id}
                                                    className={`cursor-pointer transition-colors ${selectedVoice === voice.id
                                                            ? 'border-primary bg-primary/5'
                                                            : 'hover:bg-muted/50'
                                                        }`}
                                                    onClick={() => onVoiceChange(voice.id)}
                                                >
                                                    <CardContent className="p-4">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex-1">
                                                                <div className="flex items-center gap-2">
                                                                    <h5 className="font-medium">{voice.name}</h5>
                                                                    {voice.category && (
                                                                        <Badge variant="secondary" className="text-xs">
                                                                            {voice.category}
                                                                        </Badge>
                                                                    )}
                                                                </div>
                                                                {voice.description && (
                                                                    <p className="text-sm text-muted-foreground mt-1">
                                                                        {voice.description}
                                                                    </p>
                                                                )}
                                                                {voice.labels && Object.keys(voice.labels).length > 0 && (
                                                                    <div className="flex gap-1 mt-2">
                                                                        {Object.entries(voice.labels).slice(0, 3).map(([key, value]) => (
                                                                            <Badge key={key} variant="outline" className="text-xs">
                                                                                {value}
                                                                            </Badge>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                            {voice.preview_url && (
                                                                <Button
                                                                    size="sm"
                                                                    variant="ghost"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        playPreview(voice.preview_url!, voice.id);
                                                                    }}
                                                                >
                                                                    <Play
                                                                        className={`h-4 w-4 ${playingPreview === voice.id ? 'animate-pulse' : ''
                                                                            }`}
                                                                    />
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </TabsContent>
                        ))}
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    );
}
