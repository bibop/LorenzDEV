'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { User } from '@/types';
import {
  Settings,
  User as UserIcon,
  Mail,
  Bell,
  Shield,
  Key,
  Smartphone,
  Globe,
  Moon,
  Sun,
  Save,
  Link2,
  Unlink,
  Check,
  X,
} from 'lucide-react';

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Form states
  const [profile, setProfile] = useState({
    full_name: '',
    email: '',
    avatar_url: '',
  });

  const [notifications, setNotifications] = useState({
    email_notifications: true,
    telegram_notifications: true,
    push_notifications: false,
  });

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
      setProfile({
        full_name: userData.full_name || '',
        email: userData.email || '',
        avatar_url: userData.avatar_url || '',
      });
    } catch (error) {
      console.error('Failed to load user:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement profile update API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      toast({
        title: 'Profilo salvato',
        description: 'Le modifiche sono state salvate con successo',
        variant: 'success',
      });
    } catch (error) {
      console.error('Failed to save profile:', error);
      toast({
        title: 'Errore',
        description: 'Impossibile salvare il profilo. Riprova.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleNotification = (type: 'email' | 'telegram' | 'push') => {
    const key = `${type}_notifications` as keyof typeof notifications;
    const newValue = !notifications[key];
    setNotifications({
      ...notifications,
      [key]: newValue,
    });
    toast({
      title: newValue ? 'Notifiche attivate' : 'Notifiche disattivate',
      description: `Le notifiche ${type === 'email' ? 'email' : type === 'telegram' ? 'Telegram' : 'push'} sono state ${newValue ? 'attivate' : 'disattivate'}`,
      variant: newValue ? 'success' : 'default',
    });
  };

  const tabs = [
    { id: 'profile', label: 'Profilo', icon: UserIcon },
    { id: 'integrations', label: 'Integrazioni', icon: Link2 },
    { id: 'notifications', label: 'Notifiche', icon: Bell },
    { id: 'security', label: 'Sicurezza', icon: Shield },
    { id: 'appearance', label: 'Aspetto', icon: Moon },
  ];

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Settings className="w-8 h-8 text-primary" />
          Impostazioni
        </h1>
        <p className="text-muted-foreground mt-1">
          Gestisci il tuo account e le preferenze
        </p>
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
          {isLoading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-muted rounded w-1/4"></div>
              <div className="h-4 bg-muted rounded w-1/2"></div>
              <div className="h-10 bg-muted rounded"></div>
              <div className="h-10 bg-muted rounded"></div>
            </div>
          ) : (
            <>
              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Profilo</h2>
                    <p className="text-muted-foreground text-sm">
                      Gestisci le informazioni del tuo profilo
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Nome Completo
                      </label>
                      <input
                        type="text"
                        value={profile.full_name}
                        onChange={(e) =>
                          setProfile({ ...profile, full_name: e.target.value })
                        }
                        className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        value={profile.email}
                        disabled
                        className="w-full px-4 py-2 rounded-lg bg-muted border border-border opacity-50 cursor-not-allowed"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        L'email non può essere modificata
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Avatar URL
                      </label>
                      <input
                        type="url"
                        value={profile.avatar_url}
                        onChange={(e) =>
                          setProfile({ ...profile, avatar_url: e.target.value })
                        }
                        placeholder="https://..."
                        className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                      />
                    </div>

                    <button
                      onClick={handleSaveProfile}
                      disabled={isSaving}
                      className="px-6 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      {isSaving ? 'Salvataggio...' : 'Salva Modifiche'}
                    </button>
                  </div>
                </div>
              )}

              {/* Integrations Tab */}
              {activeTab === 'integrations' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Integrazioni</h2>
                    <p className="text-muted-foreground text-sm">
                      Collega i tuoi account e servizi
                    </p>
                  </div>

                  <div className="space-y-4">
                    {/* Telegram */}
                    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#0088cc] rounded-lg flex items-center justify-center">
                          <Smartphone className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <p className="font-medium">Telegram</p>
                          <p className="text-sm text-muted-foreground">
                            {user?.telegram_chat_id
                              ? 'Collegato'
                              : 'Non collegato'}
                          </p>
                        </div>
                      </div>
                      <button
                        className={`px-4 py-2 rounded-lg transition ${
                          user?.telegram_chat_id
                            ? 'bg-destructive/10 text-destructive hover:bg-destructive/20'
                            : 'lorenz-gradient text-white hover:opacity-90'
                        }`}
                      >
                        {user?.telegram_chat_id ? (
                          <>
                            <Unlink className="w-4 h-4 inline mr-2" />
                            Scollega
                          </>
                        ) : (
                          <>
                            <Link2 className="w-4 h-4 inline mr-2" />
                            Collega
                          </>
                        )}
                      </button>
                    </div>

                    {/* Google */}
                    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                          <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                          </svg>
                        </div>
                        <div>
                          <p className="font-medium">Google</p>
                          <p className="text-sm text-muted-foreground">
                            Email & Calendar
                          </p>
                        </div>
                      </div>
                      <button className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition">
                        <Link2 className="w-4 h-4 inline mr-2" />
                        Collega
                      </button>
                    </div>

                    {/* Microsoft */}
                    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#00a4ef] rounded-lg flex items-center justify-center">
                          <Globe className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <p className="font-medium">Microsoft 365</p>
                          <p className="text-sm text-muted-foreground">
                            Outlook & OneDrive
                          </p>
                        </div>
                      </div>
                      <button className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition">
                        <Link2 className="w-4 h-4 inline mr-2" />
                        Collega
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Notifiche</h2>
                    <p className="text-muted-foreground text-sm">
                      Configura come ricevere le notifiche
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                      <div>
                        <p className="font-medium">Notifiche Email</p>
                        <p className="text-sm text-muted-foreground">
                          Ricevi aggiornamenti via email
                        </p>
                      </div>
                      <button
                        onClick={() => handleToggleNotification('email')}
                        className={`w-12 h-6 rounded-full transition ${
                          notifications.email_notifications
                            ? 'bg-primary'
                            : 'bg-muted-foreground/30'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 bg-white rounded-full transition-transform ${
                            notifications.email_notifications
                              ? 'translate-x-6'
                              : 'translate-x-0.5'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                      <div>
                        <p className="font-medium">Notifiche Telegram</p>
                        <p className="text-sm text-muted-foreground">
                          Ricevi messaggi su Telegram
                        </p>
                      </div>
                      <button
                        onClick={() => handleToggleNotification('telegram')}
                        className={`w-12 h-6 rounded-full transition ${
                          notifications.telegram_notifications
                            ? 'bg-primary'
                            : 'bg-muted-foreground/30'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 bg-white rounded-full transition-transform ${
                            notifications.telegram_notifications
                              ? 'translate-x-6'
                              : 'translate-x-0.5'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Security Tab */}
              {activeTab === 'security' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Sicurezza</h2>
                    <p className="text-muted-foreground text-sm">
                      Gestisci la sicurezza del tuo account
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-3 mb-4">
                        <Key className="w-5 h-5 text-primary" />
                        <div>
                          <p className="font-medium">Cambia Password</p>
                          <p className="text-sm text-muted-foreground">
                            Aggiorna la tua password
                          </p>
                        </div>
                      </div>
                      <button className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition">
                        Cambia Password
                      </button>
                    </div>

                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-center gap-3 mb-4">
                        <Shield className="w-5 h-5 text-primary" />
                        <div>
                          <p className="font-medium">Autenticazione a Due Fattori</p>
                          <p className="text-sm text-muted-foreground">
                            Aggiungi un livello extra di sicurezza
                          </p>
                        </div>
                      </div>
                      <button className="px-4 py-2 lorenz-gradient text-white rounded-lg hover:opacity-90 transition">
                        Attiva 2FA
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Appearance Tab */}
              {activeTab === 'appearance' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Aspetto</h2>
                    <p className="text-muted-foreground text-sm">
                      Personalizza l'interfaccia
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <p className="font-medium mb-3">Tema</p>
                      <div className="flex gap-4">
                        <button className="flex-1 p-4 bg-muted rounded-lg border-2 border-primary flex flex-col items-center gap-2">
                          <Moon className="w-6 h-6" />
                          <span className="text-sm">Scuro</span>
                        </button>
                        <button className="flex-1 p-4 bg-muted rounded-lg border-2 border-transparent hover:border-border flex flex-col items-center gap-2">
                          <Sun className="w-6 h-6" />
                          <span className="text-sm">Chiaro</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
