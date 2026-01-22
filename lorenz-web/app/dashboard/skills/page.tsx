'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Skill, SkillResult, EmergentSkill } from '@/types';
import {
  Sparkles,
  Image,
  Search,
  FileText,
  Code,
  Mail,
  Calendar,
  Play,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
} from 'lucide-react';

const skillIcons: Record<string, any> = {
  image_generation: Image,
  web_search: Search,
  presentation: FileText,
  document_generation: FileText,
  code_analysis: Code,
  email_draft: Mail,
  calendar: Calendar,
  default: Sparkles,
};

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [emergentSkills, setEmergentSkills] = useState<EmergentSkill[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);
  const [result, setResult] = useState<SkillResult | null>(null);

  // Quick execute form
  const [quickPrompt, setQuickPrompt] = useState('');

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    setIsLoading(true);
    try {
      const [skillsData, emergentData] = await Promise.all([
        api.getSkills(),
        api.getEmergentSkills(),
      ]);
      setSkills(skillsData);
      setEmergentSkills(emergentData);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteSkill = async (skillName: string, params: Record<string, any> = {}) => {
    setExecuting(skillName);
    setResult(null);
    try {
      const response = await api.executeSkill(skillName, params);
      setResult(response);
    } catch (error) {
      setResult({
        success: false,
        skill_name: skillName,
        result_type: 'error',
        data: null,
        error: (error as Error).message,
        execution_time: 0,
      });
    } finally {
      setExecuting(null);
    }
  };

  const handleQuickExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickPrompt.trim()) return;

    setExecuting('auto');
    setResult(null);
    try {
      const response = await api.autoExecuteSkill(quickPrompt);
      setResult(response);
      setQuickPrompt('');
    } catch (error) {
      setResult({
        success: false,
        skill_name: 'auto',
        result_type: 'error',
        data: null,
        error: (error as Error).message,
        execution_time: 0,
      });
    } finally {
      setExecuting(null);
    }
  };

  // Group skills by category
  const godSkills = skills.filter((s) => s.type === 'god');

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-primary" />
          Skills
        </h1>
        <p className="text-muted-foreground mt-1">
          Esegui azioni avanzate con le skill di LORENZ
        </p>
      </div>

      {/* Quick Execute */}
      <div className="bg-card border border-border rounded-xl p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary" />
          Esecuzione Rapida
        </h2>
        <p className="text-muted-foreground text-sm mb-4">
          Descrivi cosa vuoi fare e LORENZ sceglierà automaticamente la skill migliore
        </p>
        <form onSubmit={handleQuickExecute} className="flex gap-3">
          <input
            type="text"
            value={quickPrompt}
            onChange={(e) => setQuickPrompt(e.target.value)}
            placeholder="Es: Genera un'immagine di un tramonto sulla spiaggia"
            className="flex-1 px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
            disabled={executing !== null}
          />
          <button
            type="submit"
            disabled={!quickPrompt.trim() || executing !== null}
            className="px-6 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2"
          >
            {executing === 'auto' ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            Esegui
          </button>
        </form>
      </div>

      {/* Result */}
      {result && (
        <div
          className={`mb-8 p-4 rounded-xl border ${
            result.success
              ? 'bg-green-500/10 border-green-500/20'
              : 'bg-destructive/10 border-destructive/20'
          }`}
        >
          <div className="flex items-start gap-3">
            {result.success ? (
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-destructive mt-0.5" />
            )}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium">
                  {result.success ? 'Skill eseguita con successo' : 'Errore nell\'esecuzione'}
                </span>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {result.execution_time.toFixed(2)}s
                </span>
              </div>
              {result.error ? (
                <p className="text-sm text-destructive">{result.error}</p>
              ) : result.result_type === 'image' ? (
                <div className="mt-2">
                  <img
                    src={result.data?.url || result.data}
                    alt="Generated"
                    className="max-w-md rounded-lg"
                  />
                </div>
              ) : (
                <pre className="text-sm bg-muted p-3 rounded-lg overflow-x-auto mt-2">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-4 animate-pulse">
              <div className="h-10 w-10 bg-muted rounded-lg mb-3"></div>
              <div className="h-5 bg-muted rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-muted rounded w-full"></div>
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* GOD Skills */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">GOD Skills (Built-in)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {godSkills.map((skill) => {
                const Icon = skillIcons[skill.name] || skillIcons.default;
                return (
                  <div
                    key={skill.name}
                    className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <Icon className="w-6 h-6 text-primary" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium mb-1">{skill.name.replace(/_/g, ' ')}</h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          {skill.description_it || skill.description}
                        </p>
                        <button
                          onClick={() => handleExecuteSkill(skill.name)}
                          disabled={executing !== null}
                          className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                          {executing === skill.name ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                          Esegui
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Emergent Skills */}
          {emergentSkills.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Skills Emergenti (Apprese)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {emergentSkills.map((skill) => (
                  <div
                    key={skill.id}
                    className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium">{skill.name}</h3>
                      <span
                        className={`px-2 py-0.5 rounded text-xs ${
                          skill.enabled
                            ? 'bg-green-500/20 text-green-500'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {skill.enabled ? 'Attiva' : 'Disattivata'}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">
                      {skill.description_it || skill.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Usata {skill.use_count} volte</span>
                      <span>{Math.round(skill.success_rate * 100)}% successo</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state for emergent skills */}
          {emergentSkills.length === 0 && (
            <div className="text-center py-8 bg-card border border-border rounded-xl">
              <Sparkles className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
              <h3 className="font-medium mb-1">Nessuna Skill Emergente</h3>
              <p className="text-sm text-muted-foreground">
                LORENZ imparerà nuove skill dalle tue interazioni
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
