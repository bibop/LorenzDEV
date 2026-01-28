/**
 * Voice API Client
 * Handles communication with LORENZ backend voice endpoints
 */

import { api } from './api';

export interface Voice {
    id: string;
    name: string;
    description?: string;
    audio_url: string;
    duration_ms: number;
    is_public: boolean;
    is_system: boolean;
    created_at: string;
}

export interface Persona {
    id: string;
    name: string;
    description?: string;
    role_prompt: string;
    voice_id: string;
    voice: Voice;
    is_public: boolean;
    is_system: boolean;
    created_at: string;
}

export interface VoiceUpload {
    name: string;
    description?: string;
    is_public: boolean;
    audio_file: File;
}

export interface PersonaCreate {
    name: string;
    description?: string;
    role_prompt: string;
    voice_id: string;
    is_public: boolean;
}

class VoiceAPIClient {
    private baseURL: string;

    constructor() {
        this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8050';
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const token = api.getToken();
        const headers: HeadersInit = {
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({
                detail: 'An unknown error occurred',
            }));
            throw new Error(error.detail);
        }

        return response.json();
    }

    // Voice methods
    async listVoices(includePublic = true, includeSystem = true): Promise<Voice[]> {
        return this.request<Voice[]>(
            `/api/v1/voices?include_public=${includePublic}&include_system=${includeSystem}`
        );
    }

    async getVoice(voiceId: string): Promise<Voice> {
        return this.request<Voice>(`/api/v1/voices/${voiceId}`);
    }

    async uploadVoice(upload: VoiceUpload): Promise<Voice> {
        const formData = new FormData();
        formData.append('name', upload.name);
        if (upload.description) formData.append('description', upload.description);
        formData.append('is_public', String(upload.is_public));
        formData.append('audio_file', upload.audio_file);

        const token = api.getToken();
        const response = await fetch(`${this.baseURL}/api/v1/voices`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(error.detail);
        }

        return response.json();
    }

    async deleteVoice(voiceId: string): Promise<void> {
        await this.request(`/api/v1/voices/${voiceId}`, { method: 'DELETE' });
    }

    // Persona methods
    async listPersonas(includePublic = true): Promise<Persona[]> {
        return this.request<Persona[]>(
            `/api/v1/voices/personas?include_public=${includePublic}`
        );
    }

    async getPersona(personaId: string): Promise<Persona> {
        return this.request<Persona>(`/api/v1/voices/personas/${personaId}`);
    }

    async createPersona(persona: PersonaCreate): Promise<Persona> {
        return this.request<Persona>('/api/v1/voices/personas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(persona),
        });
    }

    async updatePersona(
        personaId: string,
        updates: Partial<PersonaCreate>
    ): Promise<Persona> {
        return this.request<Persona>(`/api/v1/voices/personas/${personaId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
        });
    }

    async deletePersona(personaId: string): Promise<void> {
        await this.request(`/api/v1/voices/personas/${personaId}`, { method: 'DELETE' });
    }
}

export const voiceAPI = new VoiceAPIClient();
