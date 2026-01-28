/**
 * Batch document upload API
 * Handles multiple file uploads with folder structure preservation
 */

import { api } from './api';

export interface BatchUploadResult {
    successful: number;
    failed: number;
    documents: Array<{
        id: string;
        filename: string;
        path?: string;
        status: 'completed' | 'failed';
        error?: string;
    }>;
}

/**
 * Upload multiple documents in batch
 * Preserves folder structure if webkitRelativePath is available
 */
export async function batchUploadDocuments(
    files: File[],
    onProgress?: (completed: number, total: number) => void
): Promise<BatchUploadResult> {
    const results: BatchUploadResult = {
        successful: 0,
        failed: 0,
        documents: [],
    };

    let completed = 0;

    // Upload files with concurrency limit (3 at a time)
    const concurrency = 3;
    for (let i = 0; i < files.length; i += concurrency) {
        const batch = files.slice(i, i + concurrency);

        await Promise.all(
            batch.map(async (file) => {
                try {
                    const formData = new FormData();
                    formData.append('file', file);

                    // Preserve folder path if available
                    if (file.webkitRelativePath) {
                        formData.append('path', file.webkitRelativePath);
                    }

                    const response = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/rag/upload`,
                        {
                            method: 'POST',
                            headers: {
                                Authorization: `Bearer ${api.getToken()}`,
                            },
                            body: formData,
                        }
                    );

                    if (response.ok) {
                        const data = await response.json();
                        results.successful++;
                        results.documents.push({
                            id: data.document_id || data.id,
                            filename: file.name,
                            path: file.webkitRelativePath,
                            status: 'completed',
                        });
                    } else {
                        results.failed++;
                        results.documents.push({
                            id: '',
                            filename: file.name,
                            path: file.webkitRelativePath,
                            status: 'failed',
                            error: `Upload failed: ${response.statusText}`,
                        });
                    }
                } catch (error) {
                    results.failed++;
                    results.documents.push({
                        id: '',
                        filename: file.name,
                        path: file.webkitRelativePath,
                        status: 'failed',
                        error: error instanceof Error ? error.message : 'Unknown error',
                    });
                }

                completed++;
                onProgress?.(completed, files.length);
            })
        );
    }

    return results;
}
