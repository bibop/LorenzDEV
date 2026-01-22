'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { DashboardStats, MNEMEStats } from '@/types';
import { formatRelativeTime } from '@/lib/utils';
import {
  MessageSquare,
  Mail,
  Sparkles,
  Brain,
  Zap,
  TrendingUp,
  Clock,
  ArrowRight,
  FileText,
  User2,
} from 'lucide-react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { ShimmeringText } from '@/components/ui/shimmering-text';

const VoiceOrb = dynamic(() => import('@/components/voice/VoiceOrb'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full rounded-full bg-gradient-to-br from-primary/30 to-secondary/30 animate-pulse" />
  )
});

const orbColors = {
  primary: '#C4B5FD',
  secondary: '#93C5FD',
  glow: '#A5B4FC'
};

export default function DashboardPage() {
  const [mnemeStats, setMnemeStats] = useState<MNEMEStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const stats = await api.getMNEMEStats();
        setMnemeStats(stats);
      } catch (error) {
        console.error('Failed to load stats:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, []);

  const statCards = [
    {
      title: 'Chat',
      value: '—',
      icon: MessageSquare,
      color: 'chip-blue',
      bgColor: 'from-blue-100 to-blue-50',
      href: '/dashboard/chat',
    },
    {
      title: 'Email',
      value: '—',
      icon: Mail,
      color: 'chip-mint',
      bgColor: 'from-emerald-100 to-emerald-50',
      href: '/dashboard/email',
    },
    {
      title: 'Skills',
      value: mnemeStats?.enabled_skills?.toString() || '—',
      icon: Sparkles,
      color: 'chip-lavender',
      bgColor: 'from-violet-100 to-violet-50',
      href: '/dashboard/skills',
    },
    {
      title: 'MNEME',
      value: mnemeStats?.total_entries?.toString() || '—',
      icon: Brain,
      color: 'chip-peach',
      bgColor: 'from-orange-100 to-orange-50',
      href: '/dashboard/knowledge',
    },
  ];

  const quickActions = [
    { label: 'Nuova Chat', icon: MessageSquare, href: '/dashboard/chat', color: 'lavender' },
    { label: 'Controlla Email', icon: Mail, href: '/dashboard/email', color: 'blue' },
    { label: 'Digital Twin', icon: User2, href: '/dashboard/twin', color: 'mint' },
    { label: 'Documenti', icon: FileText, href: '/dashboard/documents', color: 'peach' },
  ];

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Welcome Section */}
      <div className="mb-8 flex items-center gap-6">
        <div className="w-20 h-20 shrink-0">
          <VoiceOrb
            state="idle"
            colors={orbColors}
            size={1}
            className="w-full h-full"
          />
        </div>
        <div>
          <ShimmeringText
            text="Benvenuto su Lorenz"
            className="text-2xl font-medium mb-1"
            shimmerColor="hsl(252 85% 78%)"
            duration={3}
          />
          <p className="text-muted-foreground">
            Il tuo assistente personale AI è pronto ad aiutarti
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Link
              key={stat.title}
              href={stat.href}
              className="group bg-card rounded-2xl p-5 shadow-soft hover:shadow-soft-lg transition-all duration-200 hover:-translate-y-0.5"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${stat.bgColor}`}>
                  <Icon className="w-5 h-5 text-foreground/70" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
              </div>
              <p className="text-2xl font-semibold mb-0.5">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.title}</p>
            </Link>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions - Takes 2 columns */}
        <div className="lg:col-span-2 bg-card rounded-2xl p-6 shadow-soft">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            Azioni Rapide
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Link
                  key={action.label}
                  href={action.href}
                  className={`p-4 rounded-xl bg-muted/30 hover:bg-muted/50 transition-smooth text-center group`}
                >
                  <div className={`w-12 h-12 mx-auto mb-3 rounded-xl chip-${action.color} flex items-center justify-center group-hover:scale-105 transition-smooth`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-sm font-medium">{action.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* System Status - Takes 1 column */}
        <div className="bg-card rounded-2xl p-6 shadow-soft">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            Stato Sistema
          </h2>
          <div className="space-y-4">
            {[
              { label: 'Backend API', status: 'online', statusText: 'Online' },
              { label: 'AI Orchestrator', status: 'online', statusText: 'Attivo' },
              { label: 'Telegram Bot', status: 'warning', statusText: 'Non Configurato' },
              { label: 'Email', status: 'warning', statusText: '0 Attive' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{item.label}</span>
                <span className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    item.status === 'online' ? 'status-online' : 'status-busy'
                  }`} />
                  <span className={`text-xs font-medium ${
                    item.status === 'online' ? 'text-accent-foreground' : 'text-[hsl(20,80%,45%)]'
                  }`}>
                    {item.statusText}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-card rounded-2xl p-6 shadow-soft">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            Attività Recente
          </h2>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-muted rounded-lg w-3/4 mb-2" />
                  <div className="h-3 bg-muted rounded-lg w-1/4" />
                </div>
              ))}
            </div>
          ) : mnemeStats?.recent_activity && mnemeStats.recent_activity.length > 0 ? (
            <div className="space-y-3">
              {mnemeStats.recent_activity.slice(0, 5).map((activity, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
                >
                  <div>
                    <p className="font-medium text-sm">{activity.title}</p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {activity.category}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {activity.date ? formatRelativeTime(activity.date) : '—'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-muted/50 flex items-center justify-center">
                <Clock className="w-6 h-6 text-muted-foreground/50" />
              </div>
              <p className="text-muted-foreground text-sm">Nessuna attività recente</p>
            </div>
          )}
        </div>

        {/* MNEME Categories */}
        <div className="lg:col-span-2 bg-card rounded-2xl p-6 shadow-soft">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Knowledge Base (MNEME)
          </h2>
          {isLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded-xl" />
              ))}
            </div>
          ) : mnemeStats?.by_category && Object.keys(mnemeStats.by_category).length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(mnemeStats.by_category).map(([category, count]) => (
                <div
                  key={category}
                  className={`p-4 rounded-xl ${getCategoryStyle(category)}`}
                >
                  <p className="text-2xl font-semibold mb-0.5">{count}</p>
                  <p className="text-sm capitalize opacity-80">
                    {category.replace('_', ' ')}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-muted/50 flex items-center justify-center">
                <Brain className="w-6 h-6 text-muted-foreground/50" />
              </div>
              <p className="text-muted-foreground text-sm mb-3">Nessuna entry nel knowledge base</p>
              <Link
                href="/dashboard/knowledge"
                className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
              >
                Inizia a costruire la memoria
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getCategoryStyle(category: string): string {
  const styles: Record<string, string> = {
    pattern: 'bg-[hsl(210,80%,95%)] text-[hsl(210,80%,35%)]',
    workflow: 'bg-[hsl(252,85%,95%)] text-[hsl(252,85%,35%)]',
    fact: 'bg-[hsl(168,70%,92%)] text-[hsl(168,70%,30%)]',
    preference: 'bg-[hsl(50,80%,92%)] text-[hsl(50,80%,30%)]',
    skill_memory: 'bg-[hsl(340,70%,95%)] text-[hsl(340,70%,35%)]',
  };
  return styles[category] || 'bg-muted text-muted-foreground';
}
