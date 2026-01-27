'use client';

import { useState, useEffect } from 'react';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { voiceAPI, Voice } from '@/lib/voice-api';
import { Mic } from 'lucide-react';

interface VoiceSelectorProps {
    value?: string;
    onChange: (voiceId: string) => void;
    disabled?: boolean;
}

export function VoiceSelector({ value, onChange, disabled = false }: VoiceSelectorProps) {
    const [voices, setVoices] = useState<Voice[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadVoices();
    }, []);

    const loadVoices = async () => {
        try {
            const data = await voiceAPI.listVoices(true, true);
            setVoices(data);
        } catch (error) {
            console.error('Failed to load voices:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mic className="h-4 w-4 animate-pulse" />
                <span>Loading voices...</span>
            </div>
        );
    }

    return (
        <Select value={value} onValueChange={onChange} disabled={disabled}>
            <SelectTrigger className="w-full">
                <div className="flex items-center gap-2">
                    <Mic className="h-4 w-4" />
                    <SelectValue placeholder="Select a voice" />
                </div>
            </SelectTrigger>
            <SelectContent>
                {voices.map((voice) => (
                    <SelectItem key={voice.id} value={voice.id}>
                        <div className="flex items-center justify-between w-full">
                            <span>{voice.name}</span>
                            {voice.is_system && (
                                <span className="text-xs text-muted-foreground ml-2">(System)</span>
                            )}
                        </div>
                    </SelectItem>
                ))}
                {voices.length === 0 && (
                    <div className="px-2 py-1.5 text-sm text-muted-foreground">
                        No voices available
                    </div>
                )}
            </SelectContent>
        </Select>
    );
}
