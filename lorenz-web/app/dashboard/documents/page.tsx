'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { formatRelativeTime } from '@/lib/utils';
import {
  Database,
  Upload,
  FileText,
  Search,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  Plus,
  Brain,
  File,
  FileImage,
  FileSpreadsheet,
  Presentation,
  Loader2,
  FolderOpen,
} from 'lucide-react';

interface Document {
  id: string;
  title: string;
  source_type: string;
  total_chunks: number;
  status: string;
  metadata: Record<string, any>;
  created_at: string;
}

interface RAGStats {
  total_documents: number;
  total_chunks: number;
  sources: Record<string, number>;
  vector_indexed: number;
  embedding_model: string;
  reranker_enabled: boolean;
}

interface UploadingFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  message?: string;
  documentId?: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [docsResponse, statsResponse] = await Promise.all([
        api.getRAGDocuments({ limit: 100 }),
        api.getRAGStats(),
      ]);
      setDocuments(docsResponse.documents || []);
      setStats(statsResponse);
    } catch (error) {
      console.error('Failed to load knowledge data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await api.searchRAG(searchQuery, { limit: 10 });
      setSearchResults(response.results || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFileSelect = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    if (fileArray.length === 0) return;

    const startIndex = uploadingFiles.length;

    // Add files to uploading queue
    const newUploadingFiles: UploadingFile[] = fileArray.map((file) => ({
      file,
      status: 'pending' as const,
    }));
    setUploadingFiles((prev) => [...prev, ...newUploadingFiles]);

    // Upload files sequentially
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      const index = startIndex + i;

      setUploadingFiles((prev) =>
        prev.map((f, idx) =>
          idx === index ? { ...f, status: 'uploading' } : f
        )
      );

      try {
        const result = await api.uploadDocument(file);
        setUploadingFiles((prev) =>
          prev.map((f, idx) =>
            idx === index
              ? { ...f, status: 'success', documentId: result.document_id, message: result.message }
              : f
          )
        );
      } catch (error: any) {
        setUploadingFiles((prev) =>
          prev.map((f, idx) =>
            idx === index
              ? { ...f, status: 'error', message: error.message || 'Upload failed' }
              : f
          )
        );
      }
    }

    // Reload documents after upload
    setTimeout(() => loadData(), 2000);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    handleFileSelect(files);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDelete = async (documentId: string) => {
    if (!confirm('Sei sicuro di voler eliminare questo documento?')) return;

    try {
      await api.deleteRAGDocument(documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
      loadData();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const clearUploadQueue = () => {
    setUploadingFiles((prev) => prev.filter((f) => f.status === 'uploading'));
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FileText className="w-5 h-5 text-red-400" />;
      case 'docx':
      case 'doc':
        return <FileText className="w-5 h-5 text-blue-400" />;
      case 'xlsx':
      case 'xls':
      case 'csv':
        return <FileSpreadsheet className="w-5 h-5 text-green-400" />;
      case 'pptx':
        return <Presentation className="w-5 h-5 text-orange-400" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'tiff':
        return <FileImage className="w-5 h-5 text-purple-400" />;
      default:
        return <File className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'indexed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-xs">
            <CheckCircle className="w-3 h-3" /> Indicizzato
          </span>
        );
      case 'indexing':
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-400 text-xs">
            <Clock className="w-3 h-3" /> In elaborazione
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-xs">
            <AlertCircle className="w-3 h-3" /> Errore
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-500/10 text-gray-400 text-xs">
            {status}
          </span>
        );
    }
  };

  const filteredDocuments = selectedFilter === 'all'
    ? documents
    : documents.filter(d => d.source_type === selectedFilter);

  const sourceTypes = Array.from(new Set(documents.map(d => d.source_type)));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="w-7 h-7 text-primary" />
            Documenti RAG
          </h1>
          <p className="text-muted-foreground mt-1">
            Carica e gestisci documenti per la Knowledge Base
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Carica Documento
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt,.md,.html,.csv,.xlsx,.xls,.pptx,.odt,.png,.jpg,.jpeg,.tiff,.rtf"
          onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
          className="hidden"
        />
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total_documents}</p>
                <p className="text-sm text-muted-foreground">Documenti</p>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <Database className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.vector_indexed}</p>
                <p className="text-sm text-muted-foreground">Vettori</p>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <Brain className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <p className="text-sm font-medium truncate" title={stats.embedding_model}>
                  {stats.embedding_model.split('/').pop()}
                </p>
                <p className="text-sm text-muted-foreground">Embedding</p>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${stats.reranker_enabled ? 'bg-green-500/10' : 'bg-gray-500/10'
                }`}>
                <CheckCircle className={`w-5 h-5 ${stats.reranker_enabled ? 'text-green-400' : 'text-gray-400'
                  }`} />
              </div>
              <div>
                <p className="text-sm font-medium">
                  {stats.reranker_enabled ? 'Attivo' : 'Off'}
                </p>
                <p className="text-sm text-muted-foreground">Reranker</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${isDragging
          ? 'border-primary bg-primary/5'
          : 'border-border hover:border-primary/50'
          }`}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
        <p className="text-lg font-medium mb-2">
          Trascina i file qui o clicca per caricare
        </p>
        <p className="text-sm text-muted-foreground">
          PDF, DOCX, TXT, MD, HTML, CSV, XLSX, PPTX, immagini (max 50MB)
        </p>
      </div>

      {/* Uploading Files */}
      {uploadingFiles.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium">File in caricamento</h3>
            <button
              onClick={clearUploadQueue}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Pulisci lista
            </button>
          </div>
          <div className="space-y-2">
            {uploadingFiles.map((uf, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-muted rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {getFileIcon(uf.file.name)}
                  <div>
                    <p className="font-medium text-sm">{uf.file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(uf.file.size / 1024 / 1024).toFixed(2)} MB
                      {uf.message && uf.status !== 'uploading' && (
                        <span className="ml-2">- {uf.message}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div>
                  {uf.status === 'pending' && (
                    <Clock className="w-5 h-5 text-muted-foreground" />
                  )}
                  {uf.status === 'uploading' && (
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  )}
                  {uf.status === 'success' && (
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  )}
                  {uf.status === 'error' && (
                    <AlertCircle className="w-5 h-5 text-red-400" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <Search className="w-4 h-4" />
          Cerca nei Documenti
        </h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Cerca documenti..."
            className="flex-1 px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
          />
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
          >
            {isSearching ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              {searchResults.length} risultati per "{searchQuery}"
            </p>
            {searchResults.map((result, idx) => (
              <div
                key={idx}
                className="p-3 bg-muted rounded-lg border border-border"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-sm">{result.title}</h4>
                  <span className="text-xs text-muted-foreground">
                    Score: {(result.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {result.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-medium flex items-center gap-2">
            <FolderOpen className="w-4 h-4" />
            Documenti ({filteredDocuments.length})
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedFilter('all')}
              className={`px-3 py-1 rounded-full text-xs transition ${selectedFilter === 'all'
                ? 'bg-primary text-white'
                : 'bg-muted hover:bg-muted/80'
                }`}
            >
              Tutti
            </button>
            {sourceTypes.map((type) => (
              <button
                key={type}
                onClick={() => setSelectedFilter(type)}
                className={`px-3 py-1 rounded-full text-xs transition ${selectedFilter === type
                  ? 'bg-primary text-white'
                  : 'bg-muted hover:bg-muted/80'
                  }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
            <p className="mt-2 text-muted-foreground">Caricamento...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-8 text-center">
            <Database className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
            <p className="text-muted-foreground">
              Nessun documento. Carica il primo documento per iniziare.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="p-4 flex items-center justify-between hover:bg-muted/50 transition"
              >
                <div className="flex items-center gap-4">
                  {getFileIcon(doc.title)}
                  <div>
                    <h4 className="font-medium">{doc.title}</h4>
                    <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                      <span>{doc.total_chunks} chunks</span>
                      <span>{formatRelativeTime(doc.created_at)}</span>
                      {getStatusBadge(doc.status)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-2 text-muted-foreground hover:text-red-400 transition"
                  title="Elimina"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
