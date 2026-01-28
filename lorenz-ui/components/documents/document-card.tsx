'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    FileText,
    FileSpreadsheet,
    FileImage,
    File as FileIcon,
    Trash2,
    Eye,
    Download,
    AlertCircle,
    CheckCircle2,
    Loader2,
} from 'lucide-react';
import type { Document } from '@/lib/document-api';
import { formatDistanceToNow } from 'date-fns';

interface DocumentCardProps {
    document: Document;
    onPreview?: (document: Document) => void;
    onDelete?: (document: Document) => void;
    onDownload?: (document: Document) => void;
}

const FILE_TYPE_ICONS: Record<string, React.ReactNode> = {
    pdf: <FileText className="h-6 w-6 text-red-500" />,
    docx: <FileText className="h-6 w-6 text-blue-500" />,
    doc: <FileText className="h-6 w-6 text-blue-500" />,
    xlsx: <FileSpreadsheet className="h-6 w-6 text-green-500" />,
    xls: <FileSpreadsheet className="h-6 w-6 text-green-500" />,
    txt: <FileIcon className="h-6 w-6 text-gray-500" />,
    md: <FileIcon className="h-6 w-6 text-gray-500" />,
    html: <FileIcon className="h-6 w-6 text-orange-500" />,
    csv: <FileSpreadsheet className="h-6 w-6 text-green-500" />,
};

const STATUS_CONFIG = {
    pending: {
        label: 'Pending',
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        variant: 'secondary' as const,
    },
    extracting: {
        label: 'Extracting',
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        variant: 'secondary' as const,
    },
    chunking: {
        label: 'Chunking',
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        variant: 'secondary' as const,
    },
    indexing: {
        label: 'Indexing',
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        variant: 'secondary' as const,
    },
    completed: {
        label: 'Ready',
        icon: <CheckCircle2 className="h-3 w-3" />,
        variant: 'default' as const,
    },
    failed: {
        label: 'Failed',
        icon: <AlertCircle className="h-3 w-3" />,
        variant: 'destructive' as const,
    },
};

export function DocumentCard({
    document,
    onPreview,
    onDelete,
    onDownload,
}: DocumentCardProps) {
    const getFileIcon = () => {
        const ext = document.metadata.filename?.split('.').pop()?.toLowerCase();
        return FILE_TYPE_ICONS[ext || ''] || <FileIcon className="h-6 w-6 text-gray-500" />;
    };

    const formatFileSize = (bytes?: number) => {
        if (!bytes) return 'Unknown size';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    };

    const formatDate = (date: string) => {
        try {
            return formatDistanceToNow(new Date(date), { addSuffix: true });
        } catch {
            return 'Unknown date';
        }
    };

    const statusConfig = STATUS_CONFIG[document.status] || STATUS_CONFIG.pending;

    return (
        <Card className="group hover:shadow-md transition-shadow">
            <CardContent className="p-4">
                <div className="space-y-3">
                    {/* Header */}
                    <div className="flex items-start gap-3">
                        {/* File Icon */}
                        <div className="flex-shrink-0 mt-1">{getFileIcon()}</div>

                        {/* Title and Metadata */}
                        <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-sm truncate" title={document.title}>
                                {document.title}
                            </h3>
                            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                <span>{formatFileSize(document.metadata.fileSize)}</span>
                                <span>•</span>
                                <span>{formatDate(document.created_at)}</span>
                            </div>
                        </div>

                        {/* Status Badge */}
                        <Badge variant={statusConfig.variant} className="flex-shrink-0">
                            <span className="flex items-center gap-1">
                                {statusConfig.icon}
                                {statusConfig.label}
                            </span>
                        </Badge>
                    </div>

                    {/* Stats */}
                    {document.status === 'completed' && (
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{document.chunk_count} chunks</span>
                            <span>•</span>
                            <span className="truncate">{document.source_type}</span>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2 border-t">
                        {document.status === 'completed' && (
                            <>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => onPreview?.(document)}
                                    className="flex-1"
                                >
                                    <Eye className="h-4 w-4 mr-2" />
                                    Preview
                                </Button>
                                {onDownload && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => onDownload(document)}
                                    >
                                        <Download className="h-4 w-4" />
                                    </Button>
                                )}
                            </>
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete?.(document)}
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
