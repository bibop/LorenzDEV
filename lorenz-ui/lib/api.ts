/**
 * LORENZ API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_URL
    : 'http://localhost:8000';

interface LoginRequest {
    email: string;
    password: string;
}

interface RegisterRequest {
    email: string;
    password: string;
    name?: string;
}

interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: {
        id: string;
        email: string;
        full_name: string;
        tenant_id: string;
    };
}

interface ApiError {
    detail: string;
}

class LorenzAPIClient {
    private baseURL: string;

    constructor(baseURL: string = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    // Token management
    getToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('lorenz_access_token');
    }

    setToken(token: string): void {
        if (typeof window === 'undefined') return;
        localStorage.setItem('lorenz_access_token', token);
    }

    getRefreshToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('lorenz_refresh_token');
    }

    setRefreshToken(token: string): void {
        if (typeof window === 'undefined') return;
        localStorage.setItem('lorenz_refresh_token', token);
    }

    clearTokens(): void {
        if (typeof window === 'undefined') return;
        localStorage.removeItem('lorenz_access_token');
        localStorage.removeItem('lorenz_refresh_token');
    }

    // Generic request handler
    async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const token = this.getToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            let errorDetail = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorDetail;
            } catch (e) {
                // If not JSON, try text
                const text = await response.text().catch(() => '');
                if (text) errorDetail = text;
            }
            throw new Error(errorDetail);
        }

        return response.json();
    }

    // Authentication
    async login(credentials: LoginRequest): Promise<AuthResponse> {
        const response = await this.request<AuthResponse>('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });

        // Store tokens
        this.setToken(response.access_token);
        this.setRefreshToken(response.refresh_token);

        return response;
    }

    async register(userData: RegisterRequest): Promise<AuthResponse> {
        const response = await this.request<AuthResponse>('/api/v1/auth/signup', {
            method: 'POST',
            body: JSON.stringify(userData),
        });

        // Store tokens
        this.setToken(response.access_token);
        this.setRefreshToken(response.refresh_token);

        return response;
    }

    async logout(): Promise<void> {
        this.clearTokens();
    }

    async getCurrentUser() {
        return this.request('/api/v1/users/me');
    }

    // Voice API
    async getVoiceProviders() {
        return this.request<any[]>('/api/v1/voice/voice-providers/');
    }

    async getProviderVoices(providerId: string) {
        return this.request<any[]>(`/api/v1/voice/voice-providers/${providerId}/voices`);
    }

    // Chat API
    async sendChatMessage(conversationId: string | undefined, message: string, attachments: any[] = []) {
        return this.request<any>('/api/v1/chat/message', {
            method: 'POST',
            body: JSON.stringify({
                conversation_id: conversationId,
                message,
                attachments,
                channel: 'web'
            }),
        });
    }

    async *sendChatMessageStream(conversationId: string | undefined, message: string, attachments: any[] = []) {
        const token = this.getToken();
        const response = await fetch(`${this.baseURL}/api/v1/chat/message/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                message,
                attachments,
                channel: 'web'
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to start stream: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) return;

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        yield data;
                    } catch (e) {
                        console.error('Failed to parse stream chunk:', e);
                    }
                }
            }
        }
    }

    // Check if user is authenticated
    isAuthenticated(): boolean {
        return !!this.getToken();
    }
}

// Export singleton instance
export const api = new LorenzAPIClient();
export type { AuthResponse, LoginRequest, RegisterRequest };
