'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  User2,
  Star,
  FolderKanban,
  Brain,
  Zap,
  Settings,
  TrendingUp,
  Plus,
  Trash2,
  Save,
  Loader2,
} from 'lucide-react';

interface TwinProfile {
  user_id: string;
  full_name: string;
  preferred_name: string;
  twin_name: string;
  autonomy_level: number;
  zodiac_sign?: string;
  ascendant?: string;
  communication_style: string;
  languages: string[];
  vip_contacts_count: number;
  active_projects_count: number;
}

interface LearningStats {
  total_events: number;
  events_by_type: Record<string, number>;
  patterns_count: number;
  top_patterns: any[];
  learning_started: string;
}

interface Project {
  name: string;
  description: string;
  priority: number;
  status: string;
  keywords: string[];
}

export default function TwinPage() {
  const [profile, setProfile] = useState<TwinProfile | null>(null);
  const [learningStats, setLearningStats] = useState<LearningStats | null>(null);
  const [vipContacts, setVipContacts] = useState<string[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [newVip, setNewVip] = useState('');
  const [newProject, setNewProject] = useState({ name: '', description: '', priority: 5 });

  // Editable profile fields
  const [editProfile, setEditProfile] = useState({
    twin_name: '',
    autonomy_level: 7,
    communication_style: 'direct',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [profileData, vipData, projectsData, statsData] = await Promise.all([
        api.getTwinProfile().catch(() => null),
        api.getVIPContacts().catch(() => ({ vip_contacts: [] })),
        api.getTwinProjects('active').catch(() => ({ projects: [] })),
        api.getTwinLearningStats().catch(() => null),
      ]);

      if (profileData) {
        setProfile(profileData);
        setEditProfile({
          twin_name: profileData.twin_name || 'LORENZ',
          autonomy_level: profileData.autonomy_level || 7,
          communication_style: profileData.communication_style || 'direct',
        });
      }
      setVipContacts(vipData.vip_contacts || []);
      setProjects(projectsData.projects || []);
      setLearningStats(statsData);
    } catch (error) {
      console.error('Failed to load Twin data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      await api.updateTwinProfile(editProfile);
      await loadData();
    } catch (error) {
      console.error('Failed to save profile:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddVip = async () => {
    if (!newVip.trim()) return;
    try {
      await api.addVIPContact(newVip.trim());
      setNewVip('');
      await loadData();
    } catch (error) {
      console.error('Failed to add VIP:', error);
    }
  };

  const handleRemoveVip = async (email: string) => {
    try {
      await api.removeVIPContact(email);
      await loadData();
    } catch (error) {
      console.error('Failed to remove VIP:', error);
    }
  };

  const handleAddProject = async () => {
    if (!newProject.name.trim()) return;
    try {
      await api.addTwinProject(newProject);
      setNewProject({ name: '', description: '', priority: 5 });
      await loadData();
    } catch (error) {
      console.error('Failed to add project:', error);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profilo Twin', icon: User2 },
    { id: 'vip', label: 'Contatti VIP', icon: Star },
    { id: 'projects', label: 'Progetti', icon: FolderKanban },
    { id: 'learning', label: 'Apprendimento', icon: Brain },
  ];

  if (isLoading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-muted rounded w-1/3"></div>
          <div className="h-4 bg-muted rounded w-1/2"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-32 bg-muted rounded-xl"></div>
            <div className="h-32 bg-muted rounded-xl"></div>
            <div className="h-32 bg-muted rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <User2 className="w-8 h-8 text-primary" />
          Human Digital Twin
        </h1>
        <p className="text-muted-foreground mt-1">
          Configura il tuo gemello digitale - impara dalle tue abitudini e anticipa i tuoi bisogni
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 lorenz-gradient rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-muted-foreground text-sm">Autonomia</span>
          </div>
          <p className="text-2xl font-bold">{profile?.autonomy_level || 7}/10</p>
        </div>

        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
              <Star className="w-5 h-5 text-yellow-500" />
            </div>
            <span className="text-muted-foreground text-sm">Contatti VIP</span>
          </div>
          <p className="text-2xl font-bold">{vipContacts.length}</p>
        </div>

        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <FolderKanban className="w-5 h-5 text-blue-500" />
            </div>
            <span className="text-muted-foreground text-sm">Progetti Attivi</span>
          </div>
          <p className="text-2xl font-bold">{projects.length}</p>
        </div>

        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-purple-500" />
            </div>
            <span className="text-muted-foreground text-sm">Pattern Appresi</span>
          </div>
          <p className="text-2xl font-bold">{learningStats?.patterns_count || 0}</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Tabs */}
        <div className="lg:w-64 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 bg-card border border-border rounded-xl p-6">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-1">Profilo del Twin</h2>
                <p className="text-muted-foreground text-sm">
                  Configura l'identita e il comportamento del tuo gemello digitale
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Nome del Twin
                  </label>
                  <input
                    type="text"
                    value={editProfile.twin_name}
                    onChange={(e) => setEditProfile({ ...editProfile, twin_name: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                    placeholder="LORENZ"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Il nome con cui il Twin si presenta
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Livello di Autonomia: {editProfile.autonomy_level}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={editProfile.autonomy_level}
                    onChange={(e) => setEditProfile({ ...editProfile, autonomy_level: parseInt(e.target.value) })}
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>Conservativo</span>
                    <span>Autonomo</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    {editProfile.autonomy_level >= 8 && 'Il Twin puo agire molto autonomamente. Prende decisioni e agisce senza chiedere.'}
                    {editProfile.autonomy_level >= 5 && editProfile.autonomy_level < 8 && 'Buon livello di autonomia. Agisce per cose standard, chiede per decisioni importanti.'}
                    {editProfile.autonomy_level < 5 && 'Autonomia limitata. Propone azioni ma aspetta conferma.'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Stile di Comunicazione
                  </label>
                  <select
                    value={editProfile.communication_style}
                    onChange={(e) => setEditProfile({ ...editProfile, communication_style: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                  >
                    <option value="direct">Diretto</option>
                    <option value="formal">Formale</option>
                    <option value="friendly">Amichevole</option>
                    <option value="professional">Professionale</option>
                  </select>
                </div>

                <button
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                  className="px-6 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2"
                >
                  {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  {isSaving ? 'Salvataggio...' : 'Salva Modifiche'}
                </button>
              </div>
            </div>
          )}

          {/* VIP Contacts Tab */}
          {activeTab === 'vip' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-1">Contatti VIP</h2>
                <p className="text-muted-foreground text-sm">
                  I contatti VIP ricevono priorita massima in tutte le comunicazioni
                </p>
              </div>

              <div className="flex gap-2">
                <input
                  type="email"
                  value={newVip}
                  onChange={(e) => setNewVip(e.target.value)}
                  placeholder="email@esempio.com"
                  className="flex-1 px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddVip()}
                />
                <button
                  onClick={handleAddVip}
                  className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Aggiungi
                </button>
              </div>

              <div className="space-y-2">
                {vipContacts.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Nessun contatto VIP. Aggiungi i contatti piu importanti qui.
                  </p>
                ) : (
                  vipContacts.map((email) => (
                    <div
                      key={email}
                      className="flex items-center justify-between p-3 bg-muted rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <Star className="w-5 h-5 text-yellow-500" />
                        <span>{email}</span>
                      </div>
                      <button
                        onClick={() => handleRemoveVip(email)}
                        className="p-2 text-destructive hover:bg-destructive/10 rounded-lg transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Projects Tab */}
          {activeTab === 'projects' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-1">Progetti</h2>
                <p className="text-muted-foreground text-sm">
                  I progetti attivi aiutano il Twin a filtrare e prioritizzare le comunicazioni
                </p>
              </div>

              <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  placeholder="Nome progetto"
                  className="w-full px-4 py-2 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                />
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  placeholder="Descrizione"
                  rows={2}
                  className="w-full px-4 py-2 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition resize-none"
                />
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <label className="text-sm">Priorita:</label>
                    <select
                      value={newProject.priority}
                      onChange={(e) => setNewProject({ ...newProject, priority: parseInt(e.target.value) })}
                      className="px-3 py-1.5 rounded-lg bg-background border border-border"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={handleAddProject}
                    className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Aggiungi Progetto
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {projects.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Nessun progetto attivo. Aggiungi i tuoi progetti per migliorare il filtraggio.
                  </p>
                ) : (
                  projects.map((project, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-muted rounded-lg"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium">{project.name}</h3>
                          <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 text-xs rounded ${
                            project.priority >= 8 ? 'bg-red-500/20 text-red-400' :
                            project.priority >= 5 ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-green-500/20 text-green-400'
                          }`}>
                            P{project.priority}
                          </span>
                          <span className="px-2 py-1 text-xs bg-primary/20 text-primary rounded">
                            {project.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Learning Tab */}
          {activeTab === 'learning' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-1">Apprendimento</h2>
                <p className="text-muted-foreground text-sm">
                  Statistiche su cosa il Twin ha imparato dalle tue interazioni
                </p>
              </div>

              {learningStats ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Eventi Totali</p>
                      <p className="text-2xl font-bold">{learningStats.total_events}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Pattern Rilevati</p>
                      <p className="text-2xl font-bold">{learningStats.patterns_count}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-medium mb-3">Eventi per Tipo</h3>
                    <div className="space-y-2">
                      {Object.entries(learningStats.events_by_type).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                          <span className="text-sm">{type.replace(/_/g, ' ')}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {learningStats.top_patterns.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-3">Pattern Principali</h3>
                      <div className="space-y-2">
                        {learningStats.top_patterns.slice(0, 5).map((pattern, idx) => (
                          <div key={idx} className="p-3 bg-muted rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">{pattern.name}</span>
                              <span className="text-sm text-muted-foreground">
                                Confidenza: {pattern.confidence}%
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground">{pattern.pattern_type}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  Il Twin sta iniziando ad apprendere. Le statistiche appariranno qui.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
