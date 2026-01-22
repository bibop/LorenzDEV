'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import SetupWizard from '@/components/setup/SetupWizard';
import { Loader2 } from 'lucide-react';

export default function SetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [userName, setUserName] = useState('');
  const [assistantName, setAssistantName] = useState('LORENZ');

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await api.getCurrentUser();
        setUserName(user.name || 'Friend');

        // Get assistant name from preferences
        if (user.preferences?.assistant_name) {
          setAssistantName(user.preferences.assistant_name);
        }

        // If onboarding is complete, redirect to dashboard
        if (user.onboarding_completed) {
          router.push('/dashboard');
          return;
        }

        setIsLoading(false);
      } catch {
        // Not logged in, redirect to login
        router.push('/login');
      }
    };

    checkAuth();
  }, [router]);

  const handleComplete = () => {
    router.push('/dashboard');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center lorenz-gradient">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen lorenz-gradient p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        {/* Welcome header */}
        <div className="text-center mb-8">
          <p className="text-sm text-muted-foreground mb-1">Welcome, {userName}</p>
        </div>

        {/* Setup Wizard Card */}
        <div className="bg-card/90 backdrop-blur-sm rounded-2xl p-6 md:p-8 shadow-2xl">
          <SetupWizard
            onComplete={handleComplete}
            assistantName={assistantName}
          />
        </div>

        {/* Skip setup option */}
        <div className="text-center mt-6">
          <button
            onClick={handleComplete}
            className="text-sm text-muted-foreground hover:text-foreground transition"
          >
            Skip setup and go to dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
