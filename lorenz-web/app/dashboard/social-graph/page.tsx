'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import ContactDetailPanel from '@/components/social-graph/ContactDetailPanel';

// Dynamic import for 3D component (SSR not supported)
const SocialGraph3D = dynamic(
  () => import('@/components/social-graph/SocialGraph3D'),
  { ssr: false, loading: () => <LoadingState /> }
);

// Types
interface GraphNode {
  id: string;
  name: string;
  email?: string;
  company?: string;
  role?: string;
  relationship_type: string;
  total_interactions: number;
  x: number;
  y: number;
  z: number;
  size: number;
  color: string;
  avatar?: string;
  linkedin?: string;
  twitter?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: { source: string; target: string; type?: string; weight?: number }[];
  stats: {
    total_contacts: number;
    total_interactions: number;
    by_relationship: Record<string, number>;
  };
}

interface Opportunity {
  id: string;
  contact_id: string;
  contact_name?: string;
  opportunity_type: string;
  title: string;
  description?: string;
  confidence_score: number;
  priority: number;
  potential_value?: string;
  status: string;
  suggested_action?: string;
}

// Mock data for development
const MOCK_DATA: GraphData = {
  nodes: [
    { id: '1', name: 'Elon Musk', email: 'elon@tesla.com', company: 'Tesla', role: 'CEO', relationship_type: 'potential_investor', total_interactions: 15, x: 12, y: 8, z: 5, size: 1.8, color: '#FFA500' },
    { id: '2', name: 'Juan Vicen', email: 'juan@zeleros.com', company: 'Zeleros', role: 'CEO', relationship_type: 'partner', total_interactions: 140, x: -8, y: 5, z: -3, size: 2.2, color: '#4CAF50' },
    { id: '3', name: 'Klaus Rudischhauser', email: 'klaus@eu.europa.eu', company: 'European Commission', role: 'Director', relationship_type: 'political_stakeholder', total_interactions: 153, x: 6, y: -10, z: 8, size: 2.0, color: '#F44336' },
    { id: '4', name: 'Juliano Santos', email: 'juliano@hyperloop.com', company: 'Hyperloop Italia', role: 'CTO', relationship_type: 'team_internal', total_interactions: 602, x: -3, y: 2, z: -2, size: 2.5, color: '#607D8B' },
    { id: '5', name: 'David Michail', email: 'david@company.com', company: 'Venture Capital', role: 'Partner', relationship_type: 'investor', total_interactions: 584, x: 15, y: 3, z: -8, size: 2.4, color: '#FFD700' },
    { id: '6', name: 'Michele D\'Ercole', email: 'michele@company.com', company: 'Partner Company', role: 'Managing Director', relationship_type: 'partner', total_interactions: 428, x: -12, y: -5, z: 10, size: 2.1, color: '#4CAF50' },
    { id: '7', name: 'Maria Rossi', email: 'maria@media.com', company: 'Sky News', role: 'Journalist', relationship_type: 'media', total_interactions: 45, x: 8, y: 12, z: -5, size: 1.2, color: '#E91E63' },
    { id: '8', name: 'Prof. Luigi Bianchi', email: 'luigi@polimi.it', company: 'Politecnico Milano', role: 'Professor', relationship_type: 'academia', total_interactions: 67, x: -15, y: 8, z: 3, size: 1.4, color: '#00BCD4' },
    { id: '9', name: 'Giuseppe Verdi', email: 'giuseppe@supplier.com', company: 'Tech Supplier', role: 'Sales Manager', relationship_type: 'supplier', total_interactions: 89, x: 5, y: -8, z: -12, size: 1.3, color: '#9C27B0' },
    { id: '10', name: 'Anna Ferrari', email: 'anna@client.com', company: 'Transport Co', role: 'CEO', relationship_type: 'potential_client', total_interactions: 32, x: -6, y: -12, z: 6, size: 1.1, color: '#03A9F4' },
    { id: '11', name: 'Marco Polo', email: 'marco@friend.com', company: '', role: '', relationship_type: 'friend', total_interactions: 156, x: 10, y: 15, z: 8, size: 1.6, color: '#795548' },
    { id: '12', name: 'Sara Conti', email: 'sara@family.com', company: '', role: 'Sister', relationship_type: 'family', total_interactions: 234, x: -2, y: 6, z: 4, size: 1.9, color: '#FF5722' },
  ],
  edges: [
    { source: '2', target: '4', type: 'colleague' },
    { source: '5', target: '6', type: 'mutual_connection' },
    { source: '3', target: '8', type: 'cc_together' },
  ],
  stats: {
    total_contacts: 1888,
    total_interactions: 15420,
    by_relationship: {
      investor: 12,
      potential_investor: 129,
      partner: 84,
      potential_partner: 45,
      client: 32,
      potential_client: 78,
      supplier: 56,
      political_stakeholder: 32,
      media: 28,
      academia: 59,
      team_internal: 35,
      friend: 89,
      family: 12,
      acquaintance: 1197,
    },
  },
};

const RELATIONSHIP_LABELS: Record<string, string> = {
  investor: 'Investitori',
  potential_investor: 'Possibili Investitori',
  partner: 'Partner',
  potential_partner: 'Possibili Partner',
  client: 'Clienti',
  potential_client: 'Possibili Clienti',
  supplier: 'Fornitori',
  political_stakeholder: 'Stakeholder Politici',
  media: 'Media',
  academia: 'Accademia',
  team_internal: 'Team Interno',
  friend: 'Amici',
  family: 'Famiglia',
  acquaintance: 'Conoscenti',
};

const RELATIONSHIP_COLORS: Record<string, string> = {
  investor: '#FFD700',
  potential_investor: '#FFA500',
  partner: '#4CAF50',
  potential_partner: '#8BC34A',
  client: '#2196F3',
  potential_client: '#03A9F4',
  supplier: '#9C27B0',
  political_stakeholder: '#F44336',
  media: '#E91E63',
  academia: '#00BCD4',
  team_internal: '#607D8B',
  friend: '#795548',
  family: '#FF5722',
  acquaintance: '#9E9E9E',
};

function LoadingState() {
  return (
    <div className="w-full h-full flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="mt-4 text-gray-400">Caricamento Social Graph...</p>
      </div>
    </div>
  );
}

export default function SocialGraphPage() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedContact, setSelectedContact] = useState<GraphNode | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [highlightedRelationship, setHighlightedRelationship] = useState<string | null>(null);
  const [showLabels, setShowLabels] = useState(false);
  const [showEdges, setShowEdges] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GraphNode[]>([]);

  // Load graph data
  useEffect(() => {
    const loadData = async () => {
      try {
        // In production, fetch from API:
        // const response = await fetch('/api/v1/social-graph/data');
        // const data = await response.json();

        // For now, use mock data
        await new Promise((resolve) => setTimeout(resolve, 1500));
        setGraphData(MOCK_DATA);
      } catch (error) {
        console.error('Error loading graph data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Handle node click
  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedContact(node);
    // Fetch full contact details and opportunities
    // In production:
    // const details = await fetch(`/api/v1/social-graph/contacts/${node.id}`);
    // const opps = await fetch(`/api/v1/social-graph/opportunities?contact_id=${node.id}`);
  }, []);

  // Handle search
  const handleSearch = useCallback(
    (query: string) => {
      setSearchQuery(query);
      if (!query.trim() || !graphData) {
        setSearchResults([]);
        return;
      }

      const q = query.toLowerCase();
      const results = graphData.nodes.filter(
        (n) =>
          n.name.toLowerCase().includes(q) ||
          n.email?.toLowerCase().includes(q) ||
          n.company?.toLowerCase().includes(q)
      );
      setSearchResults(results.slice(0, 10));
    },
    [graphData]
  );

  // Handle relationship filter
  const handleRelationshipClick = useCallback((relType: string) => {
    setHighlightedRelationship((current) => (current === relType ? null : relType));
  }, []);

  if (isLoading) {
    return (
      <div className="h-screen w-full">
        <LoadingState />
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <p className="text-gray-400">Nessun dato disponibile</p>
          <button className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg">
            Importa Contatti
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full relative overflow-hidden bg-gray-900">
      {/* 3D Graph */}
      <div className="absolute inset-0">
        <SocialGraph3D
          data={graphData}
          onNodeClick={handleNodeClick}
          showLabels={showLabels}
          showEdges={showEdges}
          highlightRelationship={highlightedRelationship}
        />
      </div>

      {/* Top Bar */}
      <div className="absolute top-0 left-0 right-0 p-4 z-10">
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Cerca contatto..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-64 px-4 py-2 bg-gray-800/80 backdrop-blur-sm border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-gray-800/95 backdrop-blur-sm border border-gray-700 rounded-lg overflow-hidden shadow-xl">
                {searchResults.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => {
                      handleNodeClick(result);
                      setSearchQuery('');
                      setSearchResults([]);
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-gray-700/50 flex items-center gap-3"
                  >
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm"
                      style={{ backgroundColor: result.color }}
                    >
                      {result.name.charAt(0)}
                    </div>
                    <div>
                      <div className="text-white text-sm">{result.name}</div>
                      {result.company && (
                        <div className="text-gray-500 text-xs">{result.company}</div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* View Controls */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={() => setShowLabels(!showLabels)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                showLabels
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800/80 text-gray-400 hover:text-white'
              }`}
            >
              Labels
            </button>
            <button
              onClick={() => setShowEdges(!showEdges)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                showEdges
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800/80 text-gray-400 hover:text-white'
              }`}
            >
              Edges
            </button>
          </div>
        </div>
      </div>

      {/* Stats Panel */}
      <div className="absolute top-20 left-4 z-10">
        <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-700">
          <h3 className="text-white font-semibold mb-3">Social Graph</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-2xl font-bold text-white">{graphData.stats.total_contacts}</div>
              <div className="text-gray-500">Contatti</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-indigo-400">
                {(graphData.stats.total_interactions / 1000).toFixed(1)}k
              </div>
              <div className="text-gray-500">Interazioni</div>
            </div>
          </div>
        </div>
      </div>

      {/* Relationship Filter */}
      <div className="absolute left-4 top-48 z-10 max-h-[calc(100vh-250px)] overflow-y-auto">
        <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-700">
          <h4 className="text-white font-semibold mb-3 text-sm">Filtra per tipo</h4>
          <div className="space-y-2">
            {Object.entries(graphData.stats.by_relationship)
              .sort((a, b) => b[1] - a[1])
              .map(([relType, count]) => (
                <button
                  key={relType}
                  onClick={() => handleRelationshipClick(relType)}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-all ${
                    highlightedRelationship === relType
                      ? 'bg-gray-700 ring-1 ring-indigo-500'
                      : 'hover:bg-gray-700/50'
                  }`}
                >
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: RELATIONSHIP_COLORS[relType] || '#9E9E9E' }}
                  />
                  <span className="text-gray-300 text-xs flex-1 truncate">
                    {RELATIONSHIP_LABELS[relType] || relType}
                  </span>
                  <span className="text-gray-500 text-xs">{count}</span>
                </button>
              ))}
          </div>
          {highlightedRelationship && (
            <button
              onClick={() => setHighlightedRelationship(null)}
              className="mt-3 w-full text-center text-xs text-indigo-400 hover:text-indigo-300"
            >
              Mostra tutti
            </button>
          )}
        </div>
      </div>

      {/* Import Button */}
      <div className="absolute bottom-4 left-4 z-10 flex gap-2">
        <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Importa Contatti
        </button>
        <button className="px-4 py-2 bg-gray-800/80 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Rileva Opportunita
        </button>
      </div>

      {/* Help tooltip */}
      <div className="absolute bottom-4 right-4 z-10">
        <div className="bg-gray-800/60 backdrop-blur-sm rounded-lg px-3 py-2 text-xs text-gray-400">
          <div>Scroll per zoom</div>
          <div>Trascina per ruotare</div>
          <div>Click su nodo per dettagli</div>
        </div>
      </div>

      {/* Contact Detail Panel */}
      {selectedContact && (
        <ContactDetailPanel
          contact={selectedContact as any}
          opportunities={opportunities.filter((o) => o.contact_id === selectedContact.id)}
          onClose={() => setSelectedContact(null)}
        />
      )}
    </div>
  );
}
