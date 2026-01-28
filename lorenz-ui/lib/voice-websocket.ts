/**
 * Voice WebSocket Client
 * Handles real-time bidirectional voice communication
 */

import { AudioChunk } from './audio-stream';

export interface VoiceMessage {
    type: 'audio' | 'transcript' | 'control' | 'error';
    data?: any;
    timestamp?: number;
}

export interface VoiceConnectionConfig {
    conversationId: string;
    personaId?: string;
    provider: 'personaplex' | 'elevenlabs';
    voiceId?: string;
    token: string;
}

export class VoiceWebSocketClient {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private isConnecting = false;
    private messageHandlers: Map<string, (message: VoiceMessage) => void> = new Map();

    constructor(private baseUrl: string) { }

    async connect(config: VoiceConnectionConfig): Promise<void> {
        if (this.ws?.readyState === WebSocket.OPEN) {
            throw new Error('Already connected');
        }

        if (this.isConnecting) {
            throw new Error('Connection in progress');
        }

        this.isConnecting = true;

        try {
            // Build WebSocket URL with query params
            const wsUrl = new URL(this.baseUrl);
            wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
            wsUrl.pathname = '/api/v1/voice/stream';
            wsUrl.searchParams.set('conversation_id', config.conversationId);
            wsUrl.searchParams.set('provider', config.provider);
            wsUrl.searchParams.set('token', config.token);
            if (config.personaId) wsUrl.searchParams.set('persona_id', config.personaId);
            if (config.voiceId) wsUrl.searchParams.set('voice_id', config.voiceId);

            return new Promise((resolve, reject) => {
                this.ws = new WebSocket(wsUrl.toString());
                this.ws.binaryType = 'arraybuffer';

                this.ws.onopen = () => {
                    console.log('Voice WebSocket connected');
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;
                    resolve();
                };

                this.ws.onclose = (event) => {
                    console.log('Voice WebSocket closed:', event.code, event.reason);
                    this.handleDisconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('Voice WebSocket error:', error);
                    this.isConnecting = false;
                    reject(error);
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event);
                };
            });
        } catch (error) {
            this.isConnecting = false;
            throw error;
        }
    }

    sendAudio(chunk: AudioChunk): void {
        if (!this.isConnected()) {
            throw new Error('Not connected');
        }

        // Send audio data as binary
        this.ws!.send(chunk.data);
    }

    sendControl(action: string, data?: any): void {
        if (!this.isConnected()) {
            throw new Error('Not connected');
        }

        const message: VoiceMessage = {
            type: 'control',
            data: { action, ...data },
            timestamp: Date.now(),
        };

        this.ws!.send(JSON.stringify(message));
    }

    onAudio(handler: (audioData: ArrayBuffer) => void): void {
        this.messageHandlers.set('audio', (message) => {
            if (message.data instanceof ArrayBuffer) {
                handler(message.data);
            }
        });
    }

    onTranscript(handler: (text: string) => void): void {
        this.messageHandlers.set('transcript', (message) => {
            if (message.data?.text) {
                handler(message.data.text);
            }
        });
    }

    onError(handler: (error: string) => void): void {
        this.messageHandlers.set('error', (message) => {
            if (message.data?.error) {
                handler(message.data.error);
            }
        });
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
    }

    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }

    private handleMessage(event: MessageEvent): void {
        // Handle binary audio data
        if (event.data instanceof ArrayBuffer) {
            const handler = this.messageHandlers.get('audio');
            if (handler) {
                handler({ type: 'audio', data: event.data });
            }
            return;
        }

        // Handle JSON messages
        try {
            const message: VoiceMessage = JSON.parse(event.data);
            const handler = this.messageHandlers.get(message.type);
            if (handler) {
                handler(message);
            }
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }

    private handleDisconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
                // Note: reconnection would need config to be stored
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
        }
    }
}

// Global instance
let voiceClient: VoiceWebSocketClient | null = null;

export function getVoiceClient(): VoiceWebSocketClient {
    if (!voiceClient) {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8050';
        voiceClient = new VoiceWebSocketClient(baseUrl);
    }
    return voiceClient;
}
