'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { KnowledgeEntry, MNEMEStats } from '@/types';
import { formatRelativeTime, getCategoryColor, getCategoryLabel, truncate } from '@/lib/utils';
import {
  Brain,
  Search,
  Plus,
  Filter,
  X,
  ChevronDown,
  Tag,
  Clock,
  Eye,
  Trash2,
} from 'lucide-react';

export default function KnowledgePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [stats, setStats] = useState<MNEMEStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // New entry form
  const [newEntry, setNewEntry] = useState({
    title: '',
    content: '',
    category: 'fact',
    tags: '',
  });

  useEffect(() => {
    loadData();
  }, [selectedCategory]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [entriesData, statsData] = await Promise.all([
        api.getKnowledgeEntries(selectedCategory || undefined),
        api.getMNEMEStats(),
      ]);
      setEntries(entriesData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load knowledge data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadData();
      return;
    }

    setIsLoading(true);
    try {
      const results = await api.searchKnowledge(searchQuery, {
        category: selectedCategory || undefined,
        semantic: true,
      });
      setEntries(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createKnowledgeEntry({
        title: newEntry.title,
        content: newEntry.content,
        category: newEntry.category,
        tags: newEntry.tags.split(',').map((t) => t.trim()).filter(Boolean),
      });
      setShowAddModal(false);
      setNewEntry({ title: '', content: '', category: 'fact', tags: '' });
      toast({
        title: 'Entry aggiunta',
        description: 'La nuova entry è stata salvata nel knowledge base',
        variant: 'success',
      });
      loadData();
    } catch (error) {
      console.error('Failed to add entry:', error);
      toast({
        title: 'Errore',
        description: 'Impossibile aggiungere la entry. Riprova.',
        variant: 'destructive',
      });
    }
  };

  const categories = ['pattern', 'workflow', 'fact', 'preference', 'skill_memory'];

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Brain className="w-8 h-8 text-primary" />
            MNEME Knowledge Base
          </h1>
          <p className="text-muted-foreground mt-1">
            Gestisci la memoria persistente di LORENZ
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Aggiungi Entry
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-muted-foreground text-sm">Totale Entries</p>
            <p className="text-2xl font-bold">{stats.total_entries}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-muted-foreground text-sm">Skills Emergenti</p>
            <p className="text-2xl font-bold">{stats.total_skills}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-muted-foreground text-sm">Skills Attive</p>
            <p className="text-2xl font-bold">{stats.enabled_skills}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-muted-foreground text-sm">Categorie</p>
            <p className="text-2xl font-bold">{Object.keys(stats.by_category).length}</p>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Cerca nel knowledge base..."
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
          />
        </div>

        {/* Category Filter */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-2 rounded-lg text-sm transition ${
              selectedCategory === null
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            }`}
          >
            Tutte
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-2 rounded-lg text-sm transition capitalize ${
                selectedCategory === cat
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              {getCategoryLabel(cat)}
            </button>
          ))}
        </div>
      </div>

      {/* Entries List */}
      {isLoading ? (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-4 animate-pulse">
              <div className="h-5 bg-muted rounded w-1/4 mb-2"></div>
              <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-muted rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12">
          <Brain className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">Nessuna entry trovata</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? 'Prova a modificare la ricerca'
              : 'Inizia ad aggiungere conoscenza al tuo LORENZ'}
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition"
          >
            Aggiungi Prima Entry
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs text-white ${getCategoryColor(
                        entry.category
                      )}`}
                    >
                      {getCategoryLabel(entry.category)}
                    </span>
                    <h3 className="font-medium">{entry.title}</h3>
                  </div>
                  <p className="text-muted-foreground text-sm mb-3">
                    {truncate(entry.content, 200)}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {entry.access_count} accessi
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatRelativeTime(entry.updated_at)}
                    </span>
                    {entry.tags.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Tag className="w-3 h-3" />
                        {entry.tags.slice(0, 3).join(', ')}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {Math.round(entry.confidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Entry Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h3 className="text-lg font-semibold">Aggiungi Knowledge Entry</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 hover:bg-muted rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddEntry} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Categoria</label>
                <select
                  value={newEntry.category}
                  onChange={(e) => setNewEntry({ ...newEntry, category: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {getCategoryLabel(cat)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Titolo</label>
                <input
                  type="text"
                  value={newEntry.title}
                  onChange={(e) => setNewEntry({ ...newEntry, title: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Contenuto</label>
                <textarea
                  value={newEntry.content}
                  onChange={(e) => setNewEntry({ ...newEntry, content: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition h-32 resize-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Tags (separati da virgola)</label>
                <input
                  type="text"
                  value={newEntry.tags}
                  onChange={(e) => setNewEntry({ ...newEntry, tags: e.target.value })}
                  placeholder="tag1, tag2, tag3"
                  className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-muted transition"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition"
                >
                  Salva
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
