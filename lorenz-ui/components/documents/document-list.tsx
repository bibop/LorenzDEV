'use client';

import { useState, useEffect } from 'react';
import { DocumentCard } from './document-card';
import { Loader2, FileText } from 'lucide-react';
import type { Document } from '@/lib/document-api';

interface DocumentListProps {
    documents: Document[];
    isLoading?: boolean;
    onPreview?: (document: Document) => void;
    onDelete?: (document: Document) => void;
    onDownload?: (document: Document) => void;
}

export function DocumentList({
    documents,
    isLoading,
    onPreview,
    onDelete,
    onDownload,
}: DocumentListProps) {
    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (documents.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="rounded-full bg-muted p-4 mb-4">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium mb-1">No documents yet</h3>
                <p className="text-sm text-muted-foreground max-w-sm">
                    Upload your first document to get started with RAG-powered search and chat
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((document) => (
                <DocumentCard
                    key={document.id}
                    document={document}
                    onPreview={onPreview}
                    onDelete={onDelete}
                    onDownload={onDownload}
                />
            ))}
        </div>
    );
}
