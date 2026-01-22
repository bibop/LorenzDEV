'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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

interface ContactDetail extends GraphNode {
  all_emails?: string[];
  phone?: string;
  all_phones?: string[];
  industry?: string;
  city?: string;
  country?: string;
  tags?: string[];
  notes?: string;
  email_interactions?: number;
  whatsapp_interactions?: number;
  linkedin_interactions?: number;
  call_interactions?: number;
  meeting_interactions?: number;
  first_interaction?: string;
  last_interaction?: string;
  ai_summary?: string;
}

interface Opportunity {
  id: string;
  opportunity_type: string;
  title: string;
  description?: string;
  confidence_score: number;
  priority: number;
  potential_value?: string;
  status: string;
  suggested_action?: string;
}

interface ContactDetailPanelProps {
  contact: ContactDetail | null;
  opportunities?: Opportunity[];
  onClose: () => void;
  onUpdateRelationship?: (contactId: string, relationshipType: string) => void;
  onAddNote?: (contactId: string, note: string) => void;
}

const RELATIONSHIP_LABELS: Record<string, string> = {
  investor: 'Investitore',
  potential_investor: 'Possibile Investitore',
  partner: 'Partner',
  potential_partner: 'Possibile Partner',
  client: 'Cliente',
  potential_client: 'Possibile Cliente',
  supplier: 'Fornitore',
  political_stakeholder: 'Stakeholder Politico',
  media: 'Media',
  academia: 'Accademia',
  team_internal: 'Team Interno',
  family: 'Famiglia',
  friend: 'Amico',
  acquaintance: 'Conoscente',
  other: 'Altro',
};

const RELATIONSHIP_COLORS: Record<string, string> = {
  investor: 'bg-yellow-500',
  potential_investor: 'bg-orange-500',
  partner: 'bg-green-500',
  potential_partner: 'bg-green-400',
  client: 'bg-blue-500',
  potential_client: 'bg-blue-400',
  supplier: 'bg-purple-500',
  political_stakeholder: 'bg-red-500',
  media: 'bg-pink-500',
  academia: 'bg-cyan-500',
  team_internal: 'bg-gray-500',
  family: 'bg-orange-600',
  friend: 'bg-amber-700',
  acquaintance: 'bg-gray-400',
  other: 'bg-gray-500',
};

export default function ContactDetailPanel({
  contact,
  opportunities = [],
  onClose,
  onUpdateRelationship,
  onAddNote,
}: ContactDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<'info' | 'interactions' | 'opportunities'>('info');
  const [isEditing, setIsEditing] = useState(false);
  const [newNote, setNewNote] = useState('');

  if (!contact) return null;

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  const contactOpportunities = opportunities.filter(
    (o) => o.status !== 'dismissed' && o.status !== 'lost'
  );

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: 400, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 400, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-[400px] bg-gray-900/95 backdrop-blur-xl border-l border-gray-800 shadow-2xl z-50 overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {/* Avatar */}
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold text-white"
                style={{ backgroundColor: contact.color }}
              >
                {contact.avatar ? (
                  <img
                    src={contact.avatar}
                    alt={contact.name}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  contact.name.charAt(0).toUpperCase()
                )}
              </div>

              <div>
                <h2 className="text-xl font-semibold text-white">{contact.name}</h2>
                {contact.role && (
                  <p className="text-gray-400 text-sm">{contact.role}</p>
                )}
                {contact.company && (
                  <p className="text-gray-500 text-sm">{contact.company}</p>
                )}
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Relationship Badge */}
          <div className="mt-4 flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium text-white ${
                RELATIONSHIP_COLORS[contact.relationship_type] || 'bg-gray-500'
              }`}
            >
              {RELATIONSHIP_LABELS[contact.relationship_type] || contact.relationship_type}
            </span>
            <span className="text-gray-500 text-sm">
              {contact.total_interactions} interazioni
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-800">
          {(['info', 'interactions', 'opportunities'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'text-indigo-400 border-b-2 border-indigo-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab === 'info' && 'Info'}
              {tab === 'interactions' && 'Interazioni'}
              {tab === 'opportunities' && `Opportunita (${contactOpportunities.length})`}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'info' && (
            <div className="space-y-6">
              {/* Contact Info */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Contatti
                </h3>
                <div className="space-y-3">
                  {contact.email && (
                    <a
                      href={`mailto:${contact.email}`}
                      className="flex items-center gap-3 text-gray-300 hover:text-white"
                    >
                      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <span className="text-sm">{contact.email}</span>
                    </a>
                  )}
                  {contact.phone && (
                    <a
                      href={`tel:${contact.phone}`}
                      className="flex items-center gap-3 text-gray-300 hover:text-white"
                    >
                      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      <span className="text-sm">{contact.phone}</span>
                    </a>
                  )}
                  {contact.linkedin && (
                    <a
                      href={contact.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 text-gray-300 hover:text-blue-400"
                    >
                      <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                      </svg>
                      <span className="text-sm">LinkedIn Profile</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Location */}
              {(contact.city || contact.country) && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Posizione
                  </h3>
                  <p className="text-gray-300 text-sm">
                    {[contact.city, contact.country].filter(Boolean).join(', ')}
                  </p>
                </div>
              )}

              {/* Tags */}
              {contact.tags && contact.tags.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Tags
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {contact.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Summary */}
              {contact.ai_summary && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    AI Summary
                  </h3>
                  <p className="text-gray-300 text-sm bg-gray-800/50 rounded-lg p-3">
                    {contact.ai_summary}
                  </p>
                </div>
              )}

              {/* Notes */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Note
                </h3>
                {contact.notes ? (
                  <p className="text-gray-300 text-sm">{contact.notes}</p>
                ) : (
                  <p className="text-gray-500 text-sm italic">Nessuna nota</p>
                )}
                <button
                  onClick={() => setIsEditing(true)}
                  className="mt-2 text-indigo-400 text-sm hover:text-indigo-300"
                >
                  + Aggiungi nota
                </button>
              </div>
            </div>
          )}

          {activeTab === 'interactions' && (
            <div className="space-y-6">
              {/* Interaction Timeline */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Timeline
                </h3>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Primo contatto:</span>
                  <span className="text-gray-200">{formatDate(contact.first_interaction)}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-gray-400">Ultimo contatto:</span>
                  <span className="text-gray-200">{formatDate(contact.last_interaction)}</span>
                </div>
              </div>

              {/* Interaction Breakdown */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Per Canale
                </h3>
                <div className="space-y-3">
                  {[
                    { label: 'Email', count: contact.email_interactions, color: 'bg-blue-500' },
                    { label: 'WhatsApp', count: contact.whatsapp_interactions, color: 'bg-green-500' },
                    { label: 'LinkedIn', count: contact.linkedin_interactions, color: 'bg-blue-700' },
                    { label: 'Chiamate', count: contact.call_interactions, color: 'bg-yellow-500' },
                    { label: 'Meeting', count: contact.meeting_interactions, color: 'bg-purple-500' },
                  ]
                    .filter((item) => item.count && item.count > 0)
                    .map((item) => (
                      <div key={item.label} className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${item.color}`} />
                        <span className="text-gray-300 text-sm flex-1">{item.label}</span>
                        <span className="text-gray-400 text-sm">{item.count}</span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Interaction Chart */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Totale Interazioni
                </h3>
                <div className="flex items-end gap-1 h-20">
                  {[
                    contact.email_interactions || 0,
                    contact.whatsapp_interactions || 0,
                    contact.linkedin_interactions || 0,
                    contact.call_interactions || 0,
                    contact.meeting_interactions || 0,
                  ].map((count, i) => {
                    const max = Math.max(
                      contact.email_interactions || 0,
                      contact.whatsapp_interactions || 0,
                      contact.linkedin_interactions || 0,
                      contact.call_interactions || 0,
                      contact.meeting_interactions || 0,
                      1
                    );
                    const height = (count / max) * 100;
                    const colors = ['bg-blue-500', 'bg-green-500', 'bg-blue-700', 'bg-yellow-500', 'bg-purple-500'];
                    return (
                      <div
                        key={i}
                        className={`flex-1 ${colors[i]} rounded-t transition-all`}
                        style={{ height: `${Math.max(height, 5)}%` }}
                      />
                    );
                  })}
                </div>
                <div className="flex text-[10px] text-gray-500 mt-1">
                  <span className="flex-1 text-center">Email</span>
                  <span className="flex-1 text-center">WA</span>
                  <span className="flex-1 text-center">LI</span>
                  <span className="flex-1 text-center">Call</span>
                  <span className="flex-1 text-center">Meet</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'opportunities' && (
            <div className="space-y-4">
              {contactOpportunities.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">
                  Nessuna opportunita identificata per questo contatto
                </p>
              ) : (
                contactOpportunities.map((opp) => (
                  <div
                    key={opp.id}
                    className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-white font-medium text-sm">{opp.title}</h4>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${
                          opp.priority >= 8
                            ? 'bg-red-500/20 text-red-400'
                            : opp.priority >= 5
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-green-500/20 text-green-400'
                        }`}
                      >
                        P{opp.priority}
                      </span>
                    </div>
                    {opp.description && (
                      <p className="text-gray-400 text-xs mb-3">{opp.description}</p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>Confidenza: {Math.round(opp.confidence_score * 100)}%</span>
                      {opp.potential_value && <span>Valore: {opp.potential_value}</span>}
                    </div>
                    {opp.suggested_action && (
                      <div className="mt-3 p-2 bg-indigo-500/10 rounded text-xs text-indigo-300">
                        <strong>Azione suggerita:</strong> {opp.suggested_action}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="p-4 border-t border-gray-800 flex gap-2">
          <button className="flex-1 py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors">
            Invia Email
          </button>
          <button className="py-2 px-4 bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors">
            Programma Call
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
