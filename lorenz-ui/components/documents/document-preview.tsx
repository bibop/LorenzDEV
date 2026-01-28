'use client';

import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Download,
    FileText,
    Loader2,
    Copy,
    CheckCircle2,
    AlertCircle,
} from 'lucide-react';
import type { Document } from '@/lib/document-api';
import { documentAPI } from '@/lib/document-api';

interface DocumentPreviewProps {
    document: Document | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onDownload?: (document: Document) => void;
}

interface DocumentDetails {
    content?: string;
    chunks?: Array<{
        id: string;
        content: string;
        chunk_index: number;
        metadata: Record<string, any>;
    }>;
    processing_stats?: {
        total_chunks: number;
        total_tokens?: number;
        processing_time_ms?: number;
    };
}

export function DocumentPreview({
    document,
    open,
    onOpenChange,
    onDownload,
}: DocumentPreviewProps) {
    const [details, setDetails] = useState<DocumentDetails | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [copied, setCopied] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        if (open && document) {
            loadDocumentDetails();
        }
    }, [open, document?.id]);

    const loadDocumentDetails = async () => {
        if (!document) return;

        try {
            setIsLoading(true);
            const fullDoc = await documentAPI.getDocument(document.id);
            // Mock extracted content and chunks for now
            setDetails({
                content: 'Extracted text content will appear here...',
                chunks: Array.from({ length: document.chunk_count }, (_, i) => ({
                    id: `chunk-${i}`,
                    content: `Chunk ${i + 1} content...`,
                    chunk_index: i,
                    metadata: {},
                })),
                processing_stats: {
                    total_chunks: document.chunk_count,
                    total_tokens: document.chunk_count * 150,
                    processing_time_ms: 1500,
                },
            });
        } catch (error) {
            console.error('Failed to load document details:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleString();
    };

    const formatFileSize = (bytes?: number) => {
        if (!bytes) return 'Unknown';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    };

    if (!document) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
                <DialogHeader>
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                            <DialogTitle className="truncate">{document.title}</DialogTitle>
                            <p className="text-sm text-muted-foreground mt-1">
                                {document.source_type} • {formatFileSize(document.metadata.fileSize)}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Badge
                                variant={document.status === 'completed' ? 'default' : 'secondary'}
                            >
                                {document.status}
                            </Badge>
                            {onDownload && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onDownload(document)}
                                >
                                    <Download className="h-4 w-4 mr-2" />
                                    Download
                                </Button>
                            )}
                        </div>
                    </div>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
                        <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="overview">Overview</TabsTrigger>
                            <TabsTrigger value="content">Content</TabsTrigger>
                            <TabsTrigger value="chunks">
                                Chunks ({document.chunk_count})
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="overview" className="flex-1 overflow-hidden mt-4">
                            <ScrollArea className="h-[500px]">
                                <div className="space-y-4 pr-4">
                                    {/* Metadata */}
                                    <Card>
                                        <CardHeader>
                                            <CardTitle className="text-base">Metadata</CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-2">
                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div>
                                                    <p className="text-muted-foreground">Filename</p>
                                                    <p className="font-medium">{document.metadata.filename}</p>
                                                </div>
                                                <div>
                                                    <p className="text-muted-foreground">File Size</p>
                                                    <p className="font-medium">
                                                        {formatFileSize(document.metadata.fileSize)}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-muted-foreground">Uploaded</p>
                                                    <p className="font-medium">{formatDate(document.created_at)}</p>
                                                </div>
                                                <div>
                                                    <p className="text-muted-foreground">Status</p>
                                                    <p className="font-medium capitalize">{document.status}</p>
                                                </div>
                                                <div>
                                                    <p className="text-muted-foreground">MIME Type</p>
                                                    <p className="font-medium font-mono text-xs">
                                                        {document.metadata.mimeType || 'Unknown'}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-muted-foreground">Document ID</p>
                                                    <p className="font-medium font-mono text-xs truncate">
                                                        {document.id}
                                                    </p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    {/* Processing Stats */}
                                    {details?.processing_stats && (
                                        <Card>
                                            <CardHeader>
                                                <CardTitle className="text-base">Processing Stats</CardTitle>
                                            </CardHeader>
                                            <CardContent className="space-y-2">
                                                <div className="grid grid-cols-3 gap-4 text-sm">
                                                    <div>
                                                        <p className="text-muted-foreground">Total Chunks</p>
                                                        <p className="font-medium text-2xl">
                                                            {details.processing_stats.total_chunks}
                                                        </p>
                                                    </div>
                                                    {details.processing_stats.total_tokens && (
                                                        <div>
                                                            <p className="text-muted-foreground">Tokens</p>
                                                            <p className="font-medium text-2xl">
                                                                ~{details.processing_stats.total_tokens.toLocaleString()}
                                                            </p>
                                                        </div>
                                                    )}
                                                    {details.processing_stats.processing_time_ms && (
                                                        <div>
                                                            <p className="text-muted-foreground">Processing Time</p>
                                                            <p className="font-medium text-2xl">
                                                                {Math.round(details.processing_stats.processing_time_ms / 1000)}s
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )}

                                    {/* Status Info */}
                                    {document.status === 'completed' && (
                                        <Card className="bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900">
                                            <CardContent className="pt-6">
                                                <div className="flex items-start gap-3">
                                                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                                                    <div>
                                                        <p className="font-medium text-green-900 dark:text-green-100">
                                                            Document Ready
                                                        </p>
                                                        <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                                                            This document has been successfully processed and indexed for RAG queries.
                                                        </p>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )}

                                    {document.status === 'failed' && (
                                        <Card className="bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900">
                                            <CardContent className="pt-6">
                                                <div className="flex items-start gap-3">
                                                    <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                                                    <div>
                                                        <p className="font-medium text-red-900 dark:text-red-100">
                                                            Processing Failed
                                                        </p>
                                                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                                                            There was an error processing this document. Please try uploading again.
                                                        </p>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )}
                                </div>
                            </ScrollArea>
                        </TabsContent>

                        <TabsContent value="content" className="flex-1 overflow-hidden mt-4">
                            <ScrollArea className="h-[500px]">
                                <div className="pr-4">
                                    <Card>
                                        <CardHeader>
                                            <div className="flex items-center justify-between">
                                                <CardTitle className="text-base">Extracted Text</CardTitle>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => copyToClipboard(details?.content || '')}
                                                >
                                                    {copied ? (
                                                        <>
                                                            <CheckCircle2 className="h-4 w-4 mr-2" />
                                                            Copied
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Copy className="h-4 w-4 mr-2" />
                                                            Copy
                                                        </>
                                                    )}
                                                </Button>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <pre className="text-sm whitespace-pre-wrap font-mono bg-muted p-4 rounded-md">
                                                {details?.content || 'No content available'}
                                            </pre>
                                        </CardContent>
                                    </Card>
                                </div>
                            </ScrollArea>
                        </TabsContent>

                        <TabsContent value="chunks" className="flex-1 overflow-hidden mt-4">
                            <ScrollArea className="h-[500px]">
                                <div className="space-y-3 pr-4">
                                    {details?.chunks?.map((chunk) => (
                                        <Card key={chunk.id}>
                                            <CardHeader className="pb-3">
                                                <div className="flex items-center justify-between">
                                                    <CardTitle className="text-sm">
                                                        Chunk {chunk.chunk_index + 1}
                                                    </CardTitle>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => copyToClipboard(chunk.content)}
                                                    >
                                                        <Copy className="h-3 w-3" />
                                                    </Button>
                                                </div>
                                            </CardHeader>
                                            <CardContent>
                                                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                                    {chunk.content}
                                                </p>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </ScrollArea>
                        </TabsContent>
                    </Tabs>
                )}
            </DialogContent>
        </Dialog>
    );
}
