/**
 * Document API Client
 * Interface for RAG document management
 */

import { api } from './api';

export interface DocumentMetadata {
    filename: string;
    fileSize: number;
    mimeType: string;
    uploadedAt: string;
    processedAt?: string;
    [key: string]: any;
}

export interface Document {
    id: string;
    title: string;
    source_type: string;
    status: 'pending' | 'extracting' | 'chunking' | 'indexing' | 'completed' | 'failed';
    chunk_count: number;
    metadata: DocumentMetadata;
    created_at: string;
}

export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
}

export interface SearchFilters {
    source_type?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
}

class DocumentAPI {
    private baseURL: string;

    constructor() {
        this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8050';
    }

    /**
     * Upload a document
     */
    async uploadDocument(
        file: File,
        onProgress?: (progress: UploadProgress) => void
    ): Promise<Document> {
        const formData = new FormData();
        formData.append('file', file);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            // Progress event
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress({
                        loaded: e.loaded,
                        total: e.total,
                        percentage: Math.round((e.loaded / e.total) * 100),
                    });
                }
            });

            // Load event
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid response format'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });

            // Error event
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });

            // Send request
            xhr.open('POST', `${this.baseURL}/api/v1/rag/upload`);
            xhr.setRequestHeader('Authorization', `Bearer ${api.getToken()}`);
            xhr.send(formData);
        });
    }

    /**
     * Get list of documents
     */
    async getDocuments(params?: {
        page?: number;
        limit?: number;
        search?: string;
        filters?: SearchFilters;
    }): Promise<{ documents: Document[]; total: number }> {
        const queryParams = new URLSearchParams();

        if (params?.page) queryParams.set('page', params.page.toString());
        if (params?.limit) queryParams.set('limit', params.limit.toString());
        if (params?.search) queryParams.set('search', params.search);
        if (params?.filters?.source_type) queryParams.set('source_type', params.filters.source_type);
        if (params?.filters?.status) queryParams.set('status', params.filters.status);

        const response = await fetch(
            `${this.baseURL}/api/v1/rag/documents?${queryParams}`,
            {
                headers: {
                    Authorization: `Bearer ${api.getToken()}`,
                },
            }
        );

        if (!response.ok) {
            throw new Error('Failed to fetch documents');
        }

        return response.json();
    }

    /**
     * Get single document
     */
    async getDocument(id: string): Promise<Document> {
        const response = await fetch(`${this.baseURL}/api/v1/rag/documents/${id}`, {
            headers: {
                Authorization: `Bearer ${api.getToken()}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch document');
        }

        return response.json();
    }

    /**
     * Delete document
     */
    async deleteDocument(id: string): Promise<void> {
        const response = await fetch(`${this.baseURL}/api/v1/rag/documents/${id}`, {
            method: 'DELETE',
            headers: {
                Authorization: `Bearer ${api.getToken()}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to delete document');
        }
    }

    /**
     * Search documents
     */
    async searchDocuments(query: string, limit: number = 10): Promise<Document[]> {
        const response = await fetch(
            `${this.baseURL}/api/v1/rag/search?query=${encodeURIComponent(query)}&limit=${limit}`,
            {
                headers: {
                    Authorization: `Bearer ${api.getToken()}`,
                },
            }
        );

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const data = await response.json();
        return data.results || [];
    }

    /**
     * Get document stats
     */
    async getStats(): Promise<{
        total_documents: number;
        total_chunks: number;
        by_status: Record<string, number>;
        by_type: Record<string, number>;
    }> {
        const response = await fetch(`${this.baseURL}/api/v1/rag/stats`, {
            headers: {
                Authorization: `Bearer ${api.getToken()}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }

        return response.json();
    }
}

// Global instance
export const documentAPI = new DocumentAPI();
