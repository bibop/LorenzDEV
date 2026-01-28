/**
 * Audio Stream Manager
 * Handles WebRTC audio capture and WebSocket streaming
 */

export interface AudioStreamConfig {
    sampleRate?: number;
    channelCount?: number;
    echoCancellation?: boolean;
    noiseSuppression?: boolean;
    autoGainControl?: boolean;
}

export interface AudioChunk {
    data: ArrayBuffer;
    timestamp: number;
}

export class AudioStreamManager {
    private mediaStream: MediaStream | null = null;
    private audioContext: AudioContext | null = null;
    private processor: ScriptProcessorNode | null = null;
    private source: MediaStreamAudioSourceNode | null = null;
    private isRecording = false;
    private onChunkCallback: ((chunk: AudioChunk) => void) | null = null;

    async startCapture(config: AudioStreamConfig = {}): Promise<void> {
        if (this.isRecording) {
            throw new Error('Already recording');
        }

        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: config.sampleRate || 16000,
                    channelCount: config.channelCount || 1,
                    echoCancellation: config.echoCancellation ?? true,
                    noiseSuppression: config.noiseSuppression ?? true,
                    autoGainControl: config.autoGainControl ?? true,
                },
                video: false,
            });

            // Create audio context
            this.audioContext = new AudioContext({
                sampleRate: config.sampleRate || 16000,
            });

            // Create audio source from stream
            this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Create processor for capturing audio data
            const bufferSize = 4096;
            this.processor = this.audioContext.createScriptProcessor(
                bufferSize,
                config.channelCount || 1,
                config.channelCount || 1
            );

            // Process audio chunks
            this.processor.onaudioprocess = (event) => {
                if (!this.isRecording || !this.onChunkCallback) return;

                const inputData = event.inputBuffer.getChannelData(0);
                const chunk: AudioChunk = {
                    data: this.float32ToInt16(inputData),
                    timestamp: Date.now(),
                };

                this.onChunkCallback(chunk);
            };

            // Connect nodes
            this.source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            this.isRecording = true;
        } catch (error) {
            this.cleanup();
            throw new Error(`Failed to start audio capture: ${error}`);
        }
    }

    stopCapture(): void {
        this.isRecording = false;
        this.cleanup();
    }

    onChunk(callback: (chunk: AudioChunk) => void): void {
        this.onChunkCallback = callback;
    }

    isActive(): boolean {
        return this.isRecording;
    }

    private float32ToInt16(buffer: Float32Array): ArrayBuffer {
        const int16 = new Int16Array(buffer.length);
        for (let i = 0; i < buffer.length; i++) {
            const s = Math.max(-1, Math.min(1, buffer[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        return int16.buffer;
    }

    private cleanup(): void {
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach((track) => track.stop());
            this.mediaStream = null;
        }
    }
}

/**
 * Audio Player
 * Plays received audio chunks
 */
export class AudioPlayer {
    private audioContext: AudioContext | null = null;
    private queue: AudioBuffer[] = [];
    private isPlaying = false;
    private nextStartTime = 0;
    private scheduledSources: AudioBufferSourceNode[] = [];

    async initialize(): Promise<void> {
        // Initialize with default sample rate, but it usually adapts to hardware
        this.audioContext = new AudioContext();
    }

    async playChunk(audioData: ArrayBuffer): Promise<void> {
        if (!this.audioContext) {
            await this.initialize();
        }

        try {
            // Check state
            if (this.audioContext?.state === 'suspended') {
                await this.audioContext.resume();
            }

            // Raw PCM handling (Int16 -> Float32)
            // ElevenLabs pcm_24000 sends raw 16-bit integers
            const int16Data = new Int16Array(audioData);
            const float32Data = new Float32Array(int16Data.length);

            // Convert Int16 to Float32 [-1.0, 1.0]
            for (let i = 0; i < int16Data.length; i++) {
                // Divide by 32768 to normalize
                float32Data[i] = int16Data[i] / 32768.0;
            }

            // Create AudioBuffer
            // We know the format is 24kHz mono from our backend request
            const audioBuffer = this.audioContext!.createBuffer(
                1, // Mono
                float32Data.length,
                24000 // Fixed sample rate for pcm_24000
            );

            // Copy data to channel
            audioBuffer.copyToChannel(float32Data, 0);

            this.scheduleBuffer(audioBuffer);
        } catch (error) {
            console.error('Failed to process PCM audio:', error);
        }
    }

    private scheduleBuffer(buffer: AudioBuffer): void {
        const ctx = this.audioContext!;
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(ctx.destination);

        // Schedule playback
        // Use a larger lookahead (latency) to handle network jitter
        const latency = 0.2; // 200ms latency to prevent stuttering

        if (this.nextStartTime < ctx.currentTime) {
            // Buffer underrun detected
            // Only reset if the gap is significant to avoid tiny re-syncs
            if (ctx.currentTime - this.nextStartTime > 0.1) {
                console.log('Buffer underrun, resyncing. Gap:', ctx.currentTime - this.nextStartTime);
                this.nextStartTime = ctx.currentTime + latency;
            } else {
                // Minor drift, just catch up
                this.nextStartTime = ctx.currentTime;
            }
        }

        console.log(`Scheduling chunk: ${buffer.duration.toFixed(3)}s at ${this.nextStartTime.toFixed(3)} (SR: ${buffer.sampleRate})`);

        source.start(this.nextStartTime);
        this.scheduledSources.push(source);

        // Advance pointer
        this.nextStartTime += buffer.duration;
    }

    stop(): void {
        this.scheduledSources.forEach(source => {
            try {
                source.stop();
            } catch (e) {
                // Ignore errors if already stopped
            }
        });
        this.scheduledSources = [];
        this.queue = [];
        this.nextStartTime = 0;
        this.isPlaying = false;
    }

    cleanup(): void {
        this.stop();
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}
