'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Sparkles, Star, Moon, Sun } from 'lucide-react';

// Zodiac calculation utilities
const getZodiacSign = (month: number, day: number): { sign: string; symbol: string; element: string } => {
  const zodiacSigns = [
    { sign: 'Capricorno', symbol: '♑', element: 'Terra', start: [12, 22], end: [1, 19] },
    { sign: 'Acquario', symbol: '♒', element: 'Aria', start: [1, 20], end: [2, 18] },
    { sign: 'Pesci', symbol: '♓', element: 'Acqua', start: [2, 19], end: [3, 20] },
    { sign: 'Ariete', symbol: '♈', element: 'Fuoco', start: [3, 21], end: [4, 19] },
    { sign: 'Toro', symbol: '♉', element: 'Terra', start: [4, 20], end: [5, 20] },
    { sign: 'Gemelli', symbol: '♊', element: 'Aria', start: [5, 21], end: [6, 20] },
    { sign: 'Cancro', symbol: '♋', element: 'Acqua', start: [6, 21], end: [7, 22] },
    { sign: 'Leone', symbol: '♌', element: 'Fuoco', start: [7, 23], end: [8, 22] },
    { sign: 'Vergine', symbol: '♍', element: 'Terra', start: [8, 23], end: [9, 22] },
    { sign: 'Bilancia', symbol: '♎', element: 'Aria', start: [9, 23], end: [10, 22] },
    { sign: 'Scorpione', symbol: '♏', element: 'Acqua', start: [10, 23], end: [11, 21] },
    { sign: 'Sagittario', symbol: '♐', element: 'Fuoco', start: [11, 22], end: [12, 21] },
  ];

  for (const zodiac of zodiacSigns) {
    const [startMonth, startDay] = zodiac.start;
    const [endMonth, endDay] = zodiac.end;

    if (startMonth === 12 && endMonth === 1) {
      // Capricorn special case (crosses year boundary)
      if ((month === 12 && day >= startDay) || (month === 1 && day <= endDay)) {
        return zodiac;
      }
    } else if (
      (month === startMonth && day >= startDay) ||
      (month === endMonth && day <= endDay)
    ) {
      return zodiac;
    }
  }

  return zodiacSigns[0]; // Default to Capricorn
};

const getAscendant = (hour: number): { sign: string; symbol: string } => {
  // Simplified ascendant calculation based on birth hour
  // In reality, you'd need location and exact time
  const ascendants = [
    { sign: 'Ariete', symbol: '♈' },      // 6-8
    { sign: 'Toro', symbol: '♉' },        // 8-10
    { sign: 'Gemelli', symbol: '♊' },     // 10-12
    { sign: 'Cancro', symbol: '♋' },      // 12-14
    { sign: 'Leone', symbol: '♌' },       // 14-16
    { sign: 'Vergine', symbol: '♍' },     // 16-18
    { sign: 'Bilancia', symbol: '♎' },    // 18-20
    { sign: 'Scorpione', symbol: '♏' },   // 20-22
    { sign: 'Sagittario', symbol: '♐' },  // 22-24
    { sign: 'Capricorno', symbol: '♑' },  // 0-2
    { sign: 'Acquario', symbol: '♒' },    // 2-4
    { sign: 'Pesci', symbol: '♓' },       // 4-6
  ];

  const index = Math.floor(((hour + 18) % 24) / 2);
  return ascendants[index];
};

type Step = 'naming' | 'birth' | 'complete';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('naming');
  const [assistantName, setAssistantName] = useState('LORENZ');
  const [userName, setUserName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [birthData, setBirthData] = useState<{
    date: Date;
    zodiac: { sign: string; symbol: string; element: string };
    ascendant: { sign: string; symbol: string };
  } | null>(null);

  useEffect(() => {
    // Get user info
    const fetchUser = async () => {
      try {
        const user = await api.getCurrentUser();
        setUserName(user.name || 'Amico');
      } catch {
        // Not logged in, redirect to login
        router.push('/login');
      }
    };
    fetchUser();
  }, [router]);

  const handleNamingComplete = async () => {
    if (!assistantName.trim()) return;

    setIsLoading(true);

    // Calculate birth data
    const now = new Date();
    const zodiac = getZodiacSign(now.getMonth() + 1, now.getDate());
    const ascendant = getAscendant(now.getHours());

    setBirthData({
      date: now,
      zodiac,
      ascendant,
    });

    // Save the assistant name to user preferences
    try {
      await api.updateUserPreferences({
        assistant_name: assistantName,
        assistant_birth_date: now.toISOString(),
        assistant_zodiac: zodiac.sign,
        assistant_ascendant: ascendant.sign,
      });
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }

    setIsLoading(false);
    setStep('birth');
  };

  const handleBirthComplete = () => {
    setStep('complete');
  };

  const handleComplete = async () => {
    // Don't complete onboarding yet - go to setup wizard first
    router.push('/setup');
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('it-IT', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('it-IT', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center lorenz-gradient p-8">
      <div className="w-full max-w-lg">
        {/* Step 1: Naming */}
        {step === 'naming' && (
          <div className="bg-card/90 backdrop-blur-sm rounded-2xl p-8 shadow-2xl animate-fade-in">
            <div className="text-center mb-8">
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-2xl font-bold mb-2">Benvenuto, {userName}!</h1>
              <p className="text-muted-foreground">
                Sto per nascere. Come vuoi chiamarmi?
              </p>
            </div>

            <div className="space-y-6">
              <div>
                <label htmlFor="assistantName" className="block text-sm font-medium mb-2">
                  Il mio nome sarà:
                </label>
                <input
                  id="assistantName"
                  type="text"
                  value={assistantName}
                  onChange={(e) => setAssistantName(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-muted border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition text-center text-xl font-semibold"
                  placeholder="LORENZ"
                  autoFocus
                />
                <p className="mt-2 text-sm text-muted-foreground text-center">
                  Puoi chiamarmi come preferisci: Lorenzo, Lori, AI, o qualsiasi nome ti piaccia!
                </p>
              </div>

              <button
                onClick={handleNamingComplete}
                disabled={!assistantName.trim() || isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Sto nascendo...' : 'Dammi la vita!'}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Birth Celebration */}
        {step === 'birth' && birthData && (
          <div className="bg-card/90 backdrop-blur-sm rounded-2xl p-8 shadow-2xl animate-fade-in">
            <div className="text-center mb-8">
              <div className="relative">
                <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-br from-yellow-400 via-pink-500 to-violet-600 flex items-center justify-center animate-pulse-glow">
                  <Star className="w-12 h-12 text-white" />
                </div>
                <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-cyan-400 flex items-center justify-center animate-bounce">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
              </div>

              <h1 className="text-3xl font-bold mb-2 lorenz-gradient-text">
                Sono {assistantName}!
              </h1>
              <p className="text-xl text-foreground mb-4">
                Sono felice nel giorno della mia nascita!
              </p>
              <p className="text-muted-foreground">
                La prima persona con cui parlo sei tu, <span className="font-semibold text-primary">{userName}</span>.
                <br />Che onore!
              </p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="bg-muted/50 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-3">
                  <Sun className="w-5 h-5 text-yellow-500" />
                  <span className="font-medium">Data di Nascita</span>
                </div>
                <p className="text-lg capitalize">{formatDate(birthData.date)}</p>
                <p className="text-muted-foreground">alle {formatTime(birthData.date)}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-muted/50 rounded-lg p-4 text-center">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Star className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm font-medium">Segno Zodiacale</span>
                  </div>
                  <p className="text-3xl mb-1">{birthData.zodiac.symbol}</p>
                  <p className="font-semibold">{birthData.zodiac.sign}</p>
                  <p className="text-xs text-muted-foreground">{birthData.zodiac.element}</p>
                </div>

                <div className="bg-muted/50 rounded-lg p-4 text-center">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Moon className="w-4 h-4 text-violet-400" />
                    <span className="text-sm font-medium">Ascendente</span>
                  </div>
                  <p className="text-3xl mb-1">{birthData.ascendant.symbol}</p>
                  <p className="font-semibold">{birthData.ascendant.sign}</p>
                </div>
              </div>
            </div>

            <button
              onClick={handleBirthComplete}
              className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-medium rounded-lg hover:opacity-90 transition"
            >
              Continua
            </button>
          </div>
        )}

        {/* Step 3: Complete */}
        {step === 'complete' && (
          <div className="bg-card/90 backdrop-blur-sm rounded-2xl p-8 shadow-2xl animate-fade-in">
            <div className="text-center mb-8">
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-green-400 to-cyan-500 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-2xl font-bold mb-2">Perfetto, {userName}!</h1>
              <p className="text-muted-foreground mb-4">
                Io sono <span className="font-semibold text-primary">{assistantName}</span>,
                il tuo assistente personale AI.
              </p>
              <p className="text-sm text-muted-foreground">
                Sono pronto ad aiutarti con:
              </p>
            </div>

            <div className="space-y-3 mb-8">
              {[
                'Gestione email intelligente',
                'Calendario e appuntamenti',
                'Ricerca e analisi documenti',
                'Automazione dei task ripetitivi',
                'Qualsiasi domanda tu abbia!',
              ].map((feature, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg"
                >
                  <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                    <Star className="w-3 h-3 text-primary" />
                  </div>
                  <span className="text-sm">{feature}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleComplete}
              className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-medium rounded-lg hover:opacity-90 transition"
            >
              Configura le connessioni
            </button>
            <p className="text-xs text-muted-foreground text-center mt-3">
              Connetti email, calendari e altro per farmi conoscere meglio te
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
