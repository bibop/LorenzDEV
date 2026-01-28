'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2, FolderOpen } from 'lucide-react';
import { documentAPI, type UploadProgress } from '@/lib/document-api';
import { cn } from '@/lib/utils';

interface FileUpload {
    file: File;
    progress: number;
    status: 'pending' | 'uploading' | 'completed' | 'failed';
    error?: string;
    documentId?: string;
}

interface DocumentUploaderProps {
    onUploadComplete?: (documentId: string) => void;
    maxFiles?: number;
    maxSize?: number; // in MB
    allowFolders?: boolean;
}

interface FolderStructure {
    name: string;
    totalFiles: number;
    totalSize: number;
}

// Supported file types
const SUPPORTED_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
    'text/html': ['.html'],
    'text/csv': ['.csv'],
};

export function DocumentUploader({
    onUploadComplete,
    maxFiles = 100,
    maxSize = 50,
    allowFolders = true,
}: DocumentUploaderProps) {
    const [uploads, setUploads] = useState<FileUpload[]>([]);
    const [isProcessingFolder, setIsProcessingFolder] = useState(false);
    const [folderStats, setFolderStats] = useState<FolderStructure | null>(null);

    const isSupportedFile = (filename: string): boolean => {
        const ext = filename.split('.').pop()?.toLowerCase();
        return ext ? Object.values(SUPPORTED_TYPES).flat().includes(`.${ext}`) : false;
    };

    const onDrop = useCallback(
        async (acceptedFiles: File[]) => {
            // Add files to upload queue
            const newUploads: FileUpload[] = acceptedFiles.map((file) => ({
                file,
                progress: 0,
                status: 'pending',
            }));

            setUploads((prev) => [...prev, ...newUploads]);

            // Upload files one by one
            for (let i = 0; i < newUploads.length; i++) {
                const upload = newUploads[i];
                await uploadFile(upload, uploads.length + i);
            }
        },
        [uploads.length]
    );

    const uploadFile = async (upload: FileUpload, index: number) => {
        try {
            // Update status to uploading
            setUploads((prev) =>
                prev.map((u, i) =>
                    i === index ? { ...u, status: 'uploading' as const } : u
                )
            );

            // Upload file
            const result = await documentAPI.uploadDocument(
                upload.file,
                (progress: UploadProgress) => {
                    setUploads((prev) =>
                        prev.map((u, i) =>
                            i === index ? { ...u, progress: progress.percentage } : u
                        )
                    );
                }
            );

            // Update status to completed
            setUploads((prev) =>
                prev.map((u, i) =>
                    i === index
                        ? {
                            ...u,
                            status: 'completed' as const,
                            progress: 100,
                            documentId: result.id,
                        }
                        : u
                )
            );

            onUploadComplete?.(result.id);
        } catch (error) {
            // Update status to failed
            setUploads((prev) =>
                prev.map((u, i) =>
                    i === index
                        ? {
                            ...u,
                            status: 'failed' as const,
                            error: error instanceof Error ? error.message : 'Upload failed',
                        }
                        : u
                )
            );
        }
    };

    const handleFolderUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        setIsProcessingFolder(true);

        // Convert FileList to array and filter supported files
        const fileArray = Array.from(files).filter((file) => isSupportedFile(file.name));

        if (fileArray.length === 0) {
            alert('No supported files found in folder');
            setIsProcessingFolder(false);
            return;
        }

        // Calculate folder stats
        const totalSize = fileArray.reduce((sum, file) => sum + file.size, 0);
        const folderName = fileArray[0]?.webkitRelativePath?.split('/')[0] || 'Folder';

        setFolderStats({
            name: folderName,
            totalFiles: fileArray.length,
            totalSize,
        });

        // Add files to upload queue
        const newUploads: FileUpload[] = fileArray.map((file) => ({
            file,
            progress: 0,
            status: 'pending',
        }));

        setUploads((prev) => [...prev, ...newUploads]);
        setIsProcessingFolder(false);

        // Upload files sequentially
        for (let i = 0; i < newUploads.length; i++) {
            const upload = newUploads[i];
            await uploadFile(upload, uploads.length + i);
        }

        // Reset folder stats after upload
        setTimeout(() => setFolderStats(null), 5000);
    };

    const removeUpload = (index: number) => {
        setUploads((prev) => prev.filter((_, i) => i !== index));
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: SUPPORTED_TYPES,
        maxFiles,
        maxSize: maxSize * 1024 * 1024,
    });

    const getFileIcon = (filename: string) => {
        return <File className="h-8 w-8 text-muted-foreground" />;
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <div className="space-y-4">
            {/* Drop Zone */}
            <Card
                {...getRootProps()}
                className={cn(
                    'border-2 border-dashed cursor-pointer transition-colors',
                    isDragActive && 'border-primary bg-primary/5',
                    'hover:border-primary/50'
                )}
            >
                <CardContent className="flex flex-col items-center justify-center p-8 text-center">
                    <input {...getInputProps()} />
                    <Upload
                        className={cn(
                            'h-12 w-12 mb-4',
                            isDragActive ? 'text-primary' : 'text-muted-foreground'
                        )}
                    />
                    {isDragActive ? (
                        <p className="text-lg font-medium">Drop files here...</p>
                    ) : (
                        <>
                            <p className="text-lg font-medium mb-2">
                                Drag & drop files here, or click to select
                            </p>
                            <p className="text-sm text-muted-foreground">
                                Supports PDF, DOCX, XLSX, PPTX, TXT, MD, HTML, CSV
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                Max {maxSize}MB per file
                            </p>
                        </>
                    )}
                </CardContent>
            </Card>

            {/* Folder Upload */}
            {allowFolders && (
                <>
                    <div className="flex items-center gap-4">
                        <div className="flex-1 border-t" />
                        <span className="text-sm text-muted-foreground">or</span>
                        <div className="flex-1 border-t" />
                    </div>

                    <div>
                        <input
                            type="file"
                            id="folder-upload"
                            // @ts-ignore - webkitdirectory is supported but not in types
                            webkitdirectory=""
                            directory=""
                            multiple
                            onChange={handleFolderUpload}
                            className="hidden"
                        />
                        <label htmlFor="folder-upload">
                            <Button
                                variant="outline"
                                className="w-full"
                                asChild
                                disabled={isProcessingFolder}
                            >
                                <span className="cursor-pointer">
                                    {isProcessingFolder ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Processing folder...
                                        </>
                                    ) : (
                                        <>
                                            <FolderOpen className="h-4 w-4 mr-2" />
                                            Upload Entire Folder
                                        </>
                                    )}
                                </span>
                            </Button>
                        </label>
                    </div>
                </>
            )}

            {/* Folder Stats */}
            {folderStats && (
                <Card className="bg-muted/50">
                    <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                            <div className="rounded-full bg-primary/10 p-2">
                                <FolderOpen className="h-4 w-4 text-primary" />
                            </div>
                            <div className="flex-1">
                                <p className="font-medium text-sm">{folderStats.name}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {folderStats.totalFiles} files • {formatFileSize(folderStats.totalSize)}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Upload List */}
            {uploads.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-sm font-medium">
                        Uploads ({uploads.filter((u) => u.status === 'completed').length}/{uploads.length})
                    </h3>
                    <div className="max-h-96 overflow-y-auto space-y-2">
                        {uploads.map((upload, index) => (
                            <Card key={index}>
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        {/* File Icon */}
                                        <div className="flex-shrink-0">
                                            {getFileIcon(upload.file.name)}
                                        </div>

                                        {/* File Info */}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm truncate">
                                                {upload.file.name}
                                            </p>
                                            {/* Show relative path for folder uploads */}
                                            {upload.file.webkitRelativePath && (
                                                <p className="text-xs text-muted-foreground truncate">
                                                    {upload.file.webkitRelativePath}
                                                </p>
                                            )}
                                            <p className="text-xs text-muted-foreground">
                                                {formatFileSize(upload.file.size)}
                                            </p>

                                            {/* Progress Bar */}
                                            {upload.status === 'uploading' && (
                                                <div className="mt-2">
                                                    <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-primary transition-all duration-300"
                                                            style={{ width: `${upload.progress}%` }}
                                                        />
                                                    </div>
                                                    <p className="text-xs text-muted-foreground mt-1">
                                                        {upload.progress}%
                                                    </p>
                                                </div>
                                            )}

                                            {/* Error Message */}
                                            {upload.status === 'failed' && upload.error && (
                                                <p className="text-xs text-destructive mt-1">
                                                    {upload.error}
                                                </p>
                                            )}
                                        </div>

                                        {/* Status Icon */}
                                        <div className="flex-shrink-0">
                                            {upload.status === 'pending' && (
                                                <Loader2 className="h-5 w-5 text-muted-foreground animate-spin" />
                                            )}
                                            {upload.status === 'uploading' && (
                                                <Loader2 className="h-5 w-5 text-primary animate-spin" />
                                            )}
                                            {upload.status === 'completed' && (
                                                <CheckCircle2 className="h-5 w-5 text-green-500" />
                                            )}
                                            {upload.status === 'failed' && (
                                                <AlertCircle className="h-5 w-5 text-destructive" />
                                            )}
                                        </div>

                                        {/* Remove Button */}
                                        {(upload.status === 'completed' || upload.status === 'failed') && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => removeUpload(index)}
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
