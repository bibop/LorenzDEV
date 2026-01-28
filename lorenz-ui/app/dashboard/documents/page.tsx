'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DocumentUploader } from '@/components/documents/document-uploader';
import { DocumentList } from '@/components/documents/document-list';
import { DocumentPreview } from '@/components/documents/document-preview';
import { DocumentSearch } from '@/components/documents/document-search';
import { Upload } from 'lucide-react';
import { documentAPI, type Document, type SearchFilters } from '@/lib/document-api';
import { api } from '@/lib/api';

export default function DocumentsPage() {
    const router = useRouter();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showUploader, setShowUploader] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchFilters, setSearchFilters] = useState<SearchFilters>({});
    const [previewDocument, setPreviewDocument] = useState<Document | null>(null);

    useEffect(() => {
        // Check authentication
        const token = api.getToken();
        if (!token) {
            router.push('/login');
            return;
        }

        loadDocuments();
    }, [router]);

    const loadDocuments = async () => {
        try {
            setIsLoading(true);
            const result = await documentAPI.getDocuments({
                limit: 50,
                search: searchQuery || undefined,
                filters: searchFilters,
            });
            setDocuments(result.documents);
        } catch (error) {
            console.error('Failed to load documents:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = (query: string, filters: SearchFilters) => {
        setSearchQuery(query);
        setSearchFilters(filters);
        // Trigger reload with new search params
        setTimeout(loadDocuments, 100);
    };

    const handleUploadComplete = () => {
        // Refresh document list
        loadDocuments();
    };

    const handleDelete = async (document: Document) => {
        if (!confirm(`Delete "${document.title}"?`)) return;

        try {
            await documentAPI.deleteDocument(document.id);
            // Remove from list
            setDocuments((prev) => prev.filter((d) => d.id !== document.id));
        } catch (error) {
            console.error('Failed to delete document:', error);
            alert('Failed to delete document');
        }
    };

    const handlePreview = (document: Document) => {
        setPreviewDocument(document);
    };

    const handleDownload = (document: Document) => {
        // TODO: Implement download from backend
        console.log('Download:', document);
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold">Documents</h1>
                            <p className="text-sm text-muted-foreground">
                                Upload and manage your knowledge base
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                onClick={() => router.push('/dashboard')}
                            >
                                Dashboard
                            </Button>
                            <Button onClick={() => setShowUploader(true)}>
                                <Upload className="h-4 w-4 mr-2" />
                                Upload
                            </Button>
                        </div>
                    </div>

                    {/* Search */}
                    <div className="mt-4">
                        <DocumentSearch onSearch={handleSearch} isLoading={isLoading} />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="container mx-auto px-4 py-8">
                {/* Stats */}
                <div className="mb-6">
                    <p className="text-sm text-muted-foreground">
                        {isLoading ? 'Loading...' : `${documents.length} documents`}
                    </p>
                </div>

                {/* Document List */}
                <DocumentList
                    documents={documents}
                    isLoading={isLoading}
                    onPreview={handlePreview}
                    onDelete={handleDelete}
                    onDownload={handleDownload}
                />
            </div>

            {/* Preview Modal */}
            <DocumentPreview
                document={previewDocument}
                open={!!previewDocument}
                onOpenChange={(open) => !open && setPreviewDocument(null)}
                onDownload={handleDownload}
            />

            {/* Upload Dialog */}
            <Dialog open={showUploader} onOpenChange={setShowUploader}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Upload Documents</DialogTitle>
                    </DialogHeader>
                    <DocumentUploader
                        onUploadComplete={() => {
                            handleUploadComplete();
                            // Keep dialog open so user can see upload status
                        }}
                        maxFiles={100}
                        maxSize={50}
                        allowFolders={true}
                    />
                </DialogContent>
            </Dialog>
        </div>
    );
}
