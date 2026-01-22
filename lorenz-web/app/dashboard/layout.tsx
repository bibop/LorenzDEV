'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { User } from '@/types';
import dynamic from 'next/dynamic';
import {
  MessageSquare,
  Brain,
  Sparkles,
  Mail,
  Settings,
  LogOut,
  Menu,
  X,
  Home,
  User2,
  Database,
  ChevronRight,
  Network,
} from 'lucide-react';

// Dynamically import VoiceOrb
const VoiceOrb = dynamic(() => import('@/components/voice/VoiceOrb'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full rounded-full bg-gradient-to-br from-primary/30 to-secondary/30 animate-pulse" />
  )
});

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: Home, color: 'lavender' },
  { href: '/dashboard/chat', label: 'Chat', icon: MessageSquare, color: 'blue' },
  { href: '/dashboard/social-graph', label: 'Social Graph', icon: Network, color: 'cyan' },
  { href: '/dashboard/twin', label: 'Digital Twin', icon: User2, color: 'mint' },
  { href: '/dashboard/knowledge', label: 'MNEME', icon: Brain, color: 'peach' },
  { href: '/dashboard/documents', label: 'Documenti', icon: Database, color: 'rose' },
  { href: '/dashboard/skills', label: 'Skills', icon: Sparkles, color: 'lavender' },
  { href: '/dashboard/email', label: 'Email', icon: Mail, color: 'blue' },
];

const orbColors = {
  primary: '#C4B5FD',
  secondary: '#93C5FD',
  glow: '#A5B4FC'
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      router.push('/login');
      return;
    }

    api.getCurrentUser()
      .then(setUser)
      .catch(() => {
        api.logout();
        router.push('/login');
      })
      .finally(() => setIsLoading(false));
  }, [router]);

  const handleLogout = () => {
    api.logout();
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16">
            <VoiceOrb
              state="thinking"
              colors={orbColors}
              size={1}
              className="w-full h-full"
            />
          </div>
          <p className="text-muted-foreground text-sm">Caricamento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-background">
      {/* Mobile menu button */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 rounded-xl bg-card shadow-soft border border-border/50"
      >
        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 bg-card/50 backdrop-blur-xl border-r border-border/50 transform transition-all duration-300 ease-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${isCollapsed ? 'w-20' : 'w-64'}`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 flex items-center justify-between">
            <Link href="/dashboard" className="flex items-center gap-3">
              <div className="w-10 h-10 shrink-0">
                <VoiceOrb
                  state="idle"
                  colors={orbColors}
                  size={0.7}
                  className="w-full h-full"
                />
              </div>
              {!isCollapsed && (
                <span className="text-xl font-medium lorenz-gradient-text">Lorenz</span>
              )}
            </Link>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:flex p-1.5 rounded-lg hover:bg-muted transition-smooth"
            >
              <ChevronRight
                size={16}
                className={`text-muted-foreground transition-transform duration-300 ${
                  isCollapsed ? '' : 'rotate-180'
                }`}
              />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsSidebarOpen(false)}
                  className={`nav-item ${isActive ? 'nav-item-active' : ''} ${
                    isCollapsed ? 'justify-center px-3' : ''
                  }`}
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon size={20} className="shrink-0" />
                  {!isCollapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          {/* Settings & User section */}
          <div className="p-3 space-y-1 border-t border-border/50">
            <Link
              href="/dashboard/settings"
              onClick={() => setIsSidebarOpen(false)}
              className={`nav-item ${pathname === '/dashboard/settings' ? 'nav-item-active' : ''} ${
                isCollapsed ? 'justify-center px-3' : ''
              }`}
              title={isCollapsed ? 'Impostazioni' : undefined}
            >
              <Settings size={20} className="shrink-0" />
              {!isCollapsed && <span>Impostazioni</span>}
            </Link>

            {/* User */}
            <div className={`flex items-center gap-3 p-3 rounded-xl bg-muted/30 ${
              isCollapsed ? 'justify-center' : ''
            }`}>
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center shrink-0">
                <span className="text-sm font-medium text-primary">
                  {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </span>
              </div>
              {!isCollapsed && (
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user?.full_name || 'Utente'}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
              )}
            </div>

            <button
              onClick={handleLogout}
              className={`nav-item w-full text-muted-foreground hover:text-destructive-foreground hover:bg-destructive/10 ${
                isCollapsed ? 'justify-center px-3' : ''
              }`}
              title={isCollapsed ? 'Esci' : undefined}
            >
              <LogOut size={20} className="shrink-0" />
              {!isCollapsed && <span>Esci</span>}
            </button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
