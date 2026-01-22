'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { EmailAccount, Email } from '@/types';
import { formatRelativeTime, truncate } from '@/lib/utils';
import {
  Mail,
  Inbox,
  Send,
  Star,
  Trash2,
  RefreshCw,
  Plus,
  Search,
  MoreVertical,
  Sparkles,
  AlertCircle,
  ArrowUp,
  Minus,
  ArrowDown,
  User2,
  Briefcase,
  MessageCircle,
  Wand2,
  Loader2,
  CheckCircle,
  Crown,
} from 'lucide-react';

type SmartInboxData = {
  categorized: {
    critical: any[];
    high: any[];
    medium: any[];
    low: any[];
  };
  stats: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    total: number;
  };
  vip_count: number;
  active_projects: number;
};

type TwinAnalysis = {
  analysis: {
    priority: string;
    actions: string[];
    sender_insights?: string;
    project_relevance?: string;
  };
  auto_response_suggested: boolean;
  auto_response_details?: any;
};

type TwinDraft = {
  draft: string;
  intent: string;
  suggested_subject: string;
};

export default function EmailPage() {
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);
  const [emails, setEmails] = useState<Email[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);

  // Smart Inbox state
  const [smartInboxMode, setSmartInboxMode] = useState(false);
  const [smartInboxData, setSmartInboxData] = useState<SmartInboxData | null>(null);
  const [isLoadingSmartInbox, setIsLoadingSmartInbox] = useState(false);

  // Twin Analysis state
  const [twinAnalysis, setTwinAnalysis] = useState<TwinAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Twin Draft state
  const [twinDraft, setTwinDraft] = useState<TwinDraft | null>(null);
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [draftIntent, setDraftIntent] = useState<string>('professional');

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      if (smartInboxMode) {
        loadSmartInbox();
      } else {
        loadEmails(selectedAccount);
      }
    }
  }, [selectedAccount, smartInboxMode]);

  const loadAccounts = async () => {
    setIsLoading(true);
    try {
      const data = await api.getEmailAccounts();
      setAccounts(data);
      if (data.length > 0) {
        setSelectedAccount(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load email accounts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadEmails = async (accountId: string) => {
    setIsLoading(true);
    try {
      const data = await api.getEmails(accountId);
      setEmails(data);
    } catch (error) {
      console.error('Failed to load emails:', error);
      setEmails([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSmartInbox = async () => {
    setIsLoadingSmartInbox(true);
    try {
      const data = await api.twinSmartInbox(selectedAccount || undefined);
      setSmartInboxData(data);
    } catch (error) {
      console.error('Failed to load smart inbox:', error);
      setSmartInboxData(null);
    } finally {
      setIsLoadingSmartInbox(false);
    }
  };

  const analyzeEmailWithTwin = async (email: Email) => {
    setIsAnalyzing(true);
    setTwinAnalysis(null);
    try {
      const analysis = await api.twinAnalyzeEmail({
        from: email.from_address,
        subject: email.subject,
        body: email.body || '',
        message_id: email.id,
      });
      setTwinAnalysis(analysis);
    } catch (error) {
      console.error('Failed to analyze email:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const generateDraftWithTwin = async (email: Email) => {
    setIsGeneratingDraft(true);
    setTwinDraft(null);
    try {
      const draft = await api.twinDraftResponse({
        original_from: email.from_address,
        original_subject: email.subject,
        original_body: email.body || '',
        intent: draftIntent,
      });
      setTwinDraft(draft);
    } catch (error) {
      console.error('Failed to generate draft:', error);
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'high':
        return <ArrowUp className="w-4 h-4 text-orange-500" />;
      case 'medium':
        return <Minus className="w-4 h-4 text-yellow-500" />;
      default:
        return <ArrowDown className="w-4 h-4 text-green-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-l-4 border-l-red-500 bg-red-500/5';
      case 'high':
        return 'border-l-4 border-l-orange-500 bg-orange-500/5';
      case 'medium':
        return 'border-l-4 border-l-yellow-500 bg-yellow-500/5';
      default:
        return 'border-l-4 border-l-green-500 bg-green-500/5';
    }
  };

  const renderSmartInboxList = () => {
    if (!smartInboxData) return null;
    const { categorized } = smartInboxData;
    const allEmails = [
      ...categorized.critical,
      ...categorized.high,
      ...categorized.medium,
      ...categorized.low,
    ];

    return (
      <div>
        {allEmails.map((email) => (
          <button
            key={email.id}
            onClick={() => setSelectedEmail(email)}
            className={`w-full p-4 border-b border-border hover:bg-muted/50 transition text-left ${
              getPriorityColor(email.twin_category === 'vip' ? 'critical' :
                email.twin_category === 'project' ? 'high' :
                email.twin_category === 'unread' ? 'medium' : 'low')
            } ${selectedEmail?.id === email.id ? 'bg-muted' : ''}`}
          >
            <div className="flex items-start justify-between mb-1">
              <div className="flex items-center gap-2">
                {email.twin_category === 'vip' && <Crown className="w-4 h-4 text-yellow-500" />}
                {email.twin_category === 'project' && <Briefcase className="w-4 h-4 text-blue-500" />}
                <span className={`font-medium text-sm`}>
                  {email.from_name || email.from_address}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(email.received_at || email.date)}
              </span>
            </div>
            <p className={`text-sm mb-1 font-medium`}>
              {truncate(email.subject, 50)}
            </p>
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground line-clamp-1">
                {truncate((email.snippet || email.body || '').replace(/<[^>]*>/g, ''), 60)}
              </p>
              <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                {email.twin_reason}
              </span>
            </div>
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 border-r border-border bg-card p-4 hidden lg:block">
        <button className="w-full px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition flex items-center justify-center gap-2 mb-6">
          <Plus className="w-5 h-5" />
          Nuova Email
        </button>

        {/* Smart Inbox Toggle */}
        <div className="mb-6 p-3 rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium">Smart Inbox</span>
            </div>
            <button
              onClick={() => setSmartInboxMode(!smartInboxMode)}
              className={`relative w-10 h-5 rounded-full transition ${
                smartInboxMode ? 'bg-primary' : 'bg-muted-foreground/30'
              }`}
            >
              <span
                className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                  smartInboxMode ? 'translate-x-5' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
          {smartInboxMode && smartInboxData && (
            <div className="text-xs text-muted-foreground space-y-1">
              <div className="flex justify-between">
                <span>VIP</span>
                <span className="text-red-500">{smartInboxData.stats.critical}</span>
              </div>
              <div className="flex justify-between">
                <span>Progetti</span>
                <span className="text-orange-500">{smartInboxData.stats.high}</span>
              </div>
              <div className="flex justify-between">
                <span>Non lette</span>
                <span className="text-yellow-500">{smartInboxData.stats.medium}</span>
              </div>
            </div>
          )}
        </div>

        <nav className="space-y-1 mb-6">
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary">
            <Inbox className="w-5 h-5" />
            <span>Inbox</span>
            <span className="ml-auto text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
              {smartInboxMode && smartInboxData ? smartInboxData.stats.total : emails.filter((e) => !e.is_read).length}
            </span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted transition text-muted-foreground">
            <Star className="w-5 h-5" />
            <span>Starred</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted transition text-muted-foreground">
            <Send className="w-5 h-5" />
            <span>Sent</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted transition text-muted-foreground">
            <Trash2 className="w-5 h-5" />
            <span>Trash</span>
          </button>
        </nav>

        {/* Accounts */}
        <div>
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Account
          </h3>
          {accounts.map((account) => (
            <button
              key={account.id}
              onClick={() => setSelectedAccount(account.id)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition text-sm ${
                selectedAccount === account.id
                  ? 'bg-muted'
                  : 'hover:bg-muted/50'
              }`}
            >
              <Mail className="w-4 h-4" />
              <span className="truncate">{account.email}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Email List / Content */}
      <div className="flex-1 flex">
        {/* Email List */}
        <div className={`w-full lg:w-96 border-r border-border ${selectedEmail ? 'hidden lg:block' : ''}`}>
          {/* Header */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-xl font-semibold flex items-center gap-2">
                {smartInboxMode && <Sparkles className="w-5 h-5 text-primary" />}
                {smartInboxMode ? 'Smart Inbox' : 'Email'}
              </h1>
              <button
                onClick={() => smartInboxMode ? loadSmartInbox() : selectedAccount && loadEmails(selectedAccount)}
                className="p-2 hover:bg-muted rounded-lg transition"
                disabled={isLoading || isLoadingSmartInbox}
              >
                <RefreshCw className={`w-5 h-5 ${(isLoading || isLoadingSmartInbox) ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Cerca email..."
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted border border-border focus:border-primary outline-none text-sm"
              />
            </div>
          </div>

          {/* Email List */}
          <div className="overflow-y-auto h-[calc(100vh-140px)]">
            {(isLoading || isLoadingSmartInbox) ? (
              <div className="p-4 space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-muted rounded w-1/2 mb-1"></div>
                    <div className="h-3 bg-muted rounded w-full"></div>
                  </div>
                ))}
              </div>
            ) : accounts.length === 0 ? (
              <div className="p-8 text-center">
                <Mail className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="font-medium mb-2">Nessun Account Email</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Collega un account email per iniziare
                </p>
                <button className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition">
                  Collega Account
                </button>
              </div>
            ) : smartInboxMode ? (
              renderSmartInboxList()
            ) : emails.length === 0 ? (
              <div className="p-8 text-center">
                <Inbox className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="font-medium mb-2">Nessuna Email</h3>
                <p className="text-sm text-muted-foreground">
                  La tua inbox è vuota
                </p>
              </div>
            ) : (
              <div>
                {emails.map((email) => (
                  <button
                    key={email.id}
                    onClick={() => setSelectedEmail(email)}
                    className={`w-full p-4 border-b border-border hover:bg-muted/50 transition text-left ${
                      !email.is_read ? 'bg-primary/5' : ''
                    } ${selectedEmail?.id === email.id ? 'bg-muted' : ''}`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className={`font-medium text-sm ${!email.is_read ? '' : 'text-muted-foreground'}`}>
                        {email.from_name || email.from_address}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatRelativeTime(email.received_at)}
                      </span>
                    </div>
                    <p className={`text-sm mb-1 ${!email.is_read ? 'font-medium' : ''}`}>
                      {truncate(email.subject, 50)}
                    </p>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {truncate(email.body.replace(/<[^>]*>/g, ''), 100)}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Email Content */}
        <div className={`flex-1 ${!selectedEmail ? 'hidden lg:flex' : 'flex'} flex-col`}>
          {selectedEmail ? (
            <>
              {/* Email Header */}
              <div className="p-4 border-b border-border">
                <button
                  onClick={() => {
                    setSelectedEmail(null);
                    setTwinAnalysis(null);
                    setTwinDraft(null);
                  }}
                  className="lg:hidden mb-4 text-sm text-primary"
                >
                  ← Torna alla lista
                </button>
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-semibold mb-2">{selectedEmail.subject}</h2>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">
                        {selectedEmail.from_name || selectedEmail.from_address}
                      </span>
                      <span>&lt;{selectedEmail.from_address}&gt;</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      A: {selectedEmail.to_addresses?.join(', ') || 'N/A'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => analyzeEmailWithTwin(selectedEmail)}
                      disabled={isAnalyzing}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition"
                    >
                      {isAnalyzing ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Sparkles className="w-4 h-4" />
                      )}
                      Analizza
                    </button>
                    <button className="p-2 hover:bg-muted rounded-lg transition">
                      <Star className="w-5 h-5" />
                    </button>
                    <button className="p-2 hover:bg-muted rounded-lg transition">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Twin Analysis Panel */}
              {twinAnalysis && (
                <div className="p-4 bg-primary/5 border-b border-border">
                  <div className="flex items-center gap-2 mb-3">
                    <User2 className="w-5 h-5 text-primary" />
                    <h3 className="font-medium">Analisi Twin</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Priorità:</span>
                      <span className="ml-2 font-medium capitalize flex items-center gap-1">
                        {getPriorityIcon(twinAnalysis.analysis.priority)}
                        {twinAnalysis.analysis.priority}
                      </span>
                    </div>
                    {twinAnalysis.auto_response_suggested && (
                      <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle className="w-4 h-4" />
                        <span>Risposta automatica suggerita</span>
                      </div>
                    )}
                  </div>
                  {twinAnalysis.analysis.actions && twinAnalysis.analysis.actions.length > 0 && (
                    <div className="mt-3">
                      <span className="text-sm text-muted-foreground">Azioni suggerite:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {twinAnalysis.analysis.actions.map((action, idx) => (
                          <span key={idx} className="px-2 py-1 text-xs rounded-full bg-primary/10 text-primary">
                            {action}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Email Body */}
              <div className="flex-1 overflow-y-auto p-6">
                <div
                  className="prose prose-sm dark:prose-invert max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: selectedEmail.body_html || selectedEmail.body?.replace(/\n/g, '<br>') || '',
                  }}
                />
              </div>

              {/* Twin Draft Section */}
              {twinDraft && (
                <div className="p-4 bg-primary/5 border-t border-border">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Wand2 className="w-5 h-5 text-primary" />
                      <h3 className="font-medium">Bozza generata da Twin</h3>
                    </div>
                    <span className="text-xs text-muted-foreground capitalize">
                      Tono: {twinDraft.intent}
                    </span>
                  </div>
                  <div className="bg-background rounded-lg p-3 text-sm whitespace-pre-wrap">
                    {twinDraft.draft}
                  </div>
                  <div className="flex justify-end gap-2 mt-3">
                    <button
                      onClick={() => setTwinDraft(null)}
                      className="px-3 py-1.5 text-sm rounded-lg hover:bg-muted transition"
                    >
                      Annulla
                    </button>
                    <button className="px-3 py-1.5 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition">
                      Usa questa bozza
                    </button>
                  </div>
                </div>
              )}

              {/* Reply Bar */}
              <div className="p-4 border-t border-border">
                <div className="flex gap-3 items-center">
                  <div className="flex-1 flex gap-2">
                    <input
                      type="text"
                      placeholder="Scrivi una risposta rapida..."
                      className="flex-1 px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary outline-none"
                    />
                  </div>
                  <select
                    value={draftIntent}
                    onChange={(e) => setDraftIntent(e.target.value)}
                    className="px-3 py-2 rounded-lg bg-muted border border-border text-sm"
                  >
                    <option value="professional">Professionale</option>
                    <option value="friendly">Amichevole</option>
                    <option value="formal">Formale</option>
                    <option value="brief">Breve</option>
                  </select>
                  <button
                    onClick={() => generateDraftWithTwin(selectedEmail)}
                    disabled={isGeneratingDraft}
                    className="px-4 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition flex items-center gap-2"
                  >
                    {isGeneratingDraft ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Wand2 className="w-5 h-5" />
                    )}
                    <span className="hidden sm:inline">Twin Draft</span>
                  </button>
                  <button className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition">
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-center">
              <div>
                <Mail className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">Seleziona un'email</h3>
                <p className="text-muted-foreground">
                  Scegli un'email dalla lista per leggerla
                </p>
                {!smartInboxMode && (
                  <button
                    onClick={() => setSmartInboxMode(true)}
                    className="mt-4 px-4 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition flex items-center gap-2 mx-auto"
                  >
                    <Sparkles className="w-5 h-5" />
                    Attiva Smart Inbox
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
