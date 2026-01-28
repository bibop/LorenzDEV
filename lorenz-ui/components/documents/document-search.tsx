'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Search, Filter, X } from 'lucide-react';
import type { SearchFilters } from '@/lib/document-api';

interface DocumentSearchProps {
    onSearch: (query: string, filters: SearchFilters) => void;
    isLoading?: boolean;
}

const FILE_TYPES = [
    { value: 'all', label: 'All Types' },
    { value: 'pdf', label: 'PDF' },
    { value: 'docx', label: 'Word (DOCX)' },
    { value: 'xlsx', label: 'Excel (XLSX)' },
    { value: 'txt', label: 'Text' },
    { value: 'md', label: 'Markdown' },
];

const STATUS_OPTIONS = [
    { value: 'all', label: 'All Status' },
    { value: 'pending', label: 'Pending' },
    { value: 'processing', label: 'Processing' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
];

export function DocumentSearch({ onSearch, isLoading }: DocumentSearchProps) {
    const [query, setQuery] = useState('');
    const [fileType, setFileType] = useState('all');
    const [status, setStatus] = useState('all');
    const [showFilters, setShowFilters] = useState(false);

    const handleSearch = () => {
        const filters: SearchFilters = {};

        if (fileType !== 'all') filters.source_type = fileType;
        if (status !== 'all') filters.status = status;

        onSearch(query, filters);
    };

    const clearFilters = () => {
        setQuery('');
        setFileType('all');
        setStatus('all');
        onSearch('', {});
    };

    const hasActiveFilters = fileType !== 'all' || status !== 'all' || query.length > 0;

    return (
        <div className="space-y-3">
            {/* Search Bar */}
            <div className="flex items-center gap-2">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="text"
                        placeholder="Search documents..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSearch();
                        }}
                        className="pl-10 pr-4"
                    />
                </div>

                <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowFilters(!showFilters)}
                    className={showFilters ? 'bg-muted' : ''}
                >
                    <Filter className="h-4 w-4" />
                </Button>

                <Button onClick={handleSearch} disabled={isLoading}>
                    {isLoading ? 'Searching...' : 'Search'}
                </Button>

                {hasActiveFilters && (
                    <Button variant="ghost" size="sm" onClick={clearFilters}>
                        <X className="h-4 w-4 mr-2" />
                        Clear
                    </Button>
                )}
            </div>

            {/* Filters */}
            {showFilters && (
                <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-md">
                    <div className="flex-1">
                        <label className="text-xs font-medium mb-1.5 block">File Type</label>
                        <Select value={fileType} onValueChange={setFileType}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {FILE_TYPES.map((type) => (
                                    <SelectItem key={type.value} value={type.value}>
                                        {type.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="flex-1">
                        <label className="text-xs font-medium mb-1.5 block">Status</label>
                        <Select value={status} onValueChange={setStatus}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {STATUS_OPTIONS.map((option) => (
                                    <SelectItem key={option.value} value={option.value}>
                                        {option.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            )}

            {/* Active Filter Badges */}
            {hasActiveFilters && !showFilters && (
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-muted-foreground">Active filters:</span>
                    {query && (
                        <Badge variant="secondary">
                            Search: "{query}"
                        </Badge>
                    )}
                    {fileType !== 'all' && (
                        <Badge variant="secondary">
                            Type: {FILE_TYPES.find((t) => t.value === fileType)?.label}
                        </Badge>
                    )}
                    {status !== 'all' && (
                        <Badge variant="secondary">
                            Status: {STATUS_OPTIONS.find((s) => s.value === status)?.label}
                        </Badge>
                    )}
                </div>
            )}
        </div>
    );
}
