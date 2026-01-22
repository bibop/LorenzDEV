'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import LorenzOrb, { useLorenzOrb } from '@/components/LorenzOrb';
import { api } from '@/lib/api';

// Profile field type
interface DiscoveredProfile {
  full_name: string;
  first_name: string;
  last_name: string;
  profession?: string;
  company?: string;
  role?: string;
  industry?: string;
  age?: number;
  birth_year?: number;
  location?: string;
  nationality?: string;
  marital_status?: string;
  has_children?: boolean;
  children_count?: number;
  linkedin_url?: string;
  twitter_handle?: string;
  wikipedia_url?: string;
  website?: string;
  bio_summary?: string;
  notable_achievements?: string[];
  education?: string;
  confidence_score: number;
  disambiguation_needed: boolean;
  disambiguation_options?: Array<{ description: string; context?: string }>;
  lorenz_introduction?: string;
}

type OnboardingStep =
  | 'greeting'
  | 'ask_name'
  | 'confirm_name'
  | 'searching'
  | 'show_profile'
  | 'disambiguation'
  | 'complete';

export default function OrbOnboardingPage() {
  const router = useRouter();
  const orb = useLorenzOrb();

  // State
  const [step, setStep] = useState<OnboardingStep>('greeting');
  const [userName, setUserName] = useState('');
  const [confirmedName, setConfirmedName] = useState('');
  const [profile, setProfile] = useState<DiscoveredProfile | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const [waitingForVoice, setWaitingForVoice] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);

  // Check speech support
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      setSpeechSupported(!!SpeechRecognitionAPI);
    }
  }, []);

  // Typewriter effect for displayed text
  const typeText = useCallback((text: string, onComplete?: () => void) => {
    setDisplayedText('');
    let i = 0;
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayedText(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        onComplete?.();
      }
    }, 30);
    return () => clearInterval(interval);
  }, []);

  // Start listening after speaking ends
  const startListeningAfterSpeak = useCallback((onResult: (transcript: string) => void) => {
    setWaitingForVoice(true);
    setTimeout(() => {
      orb.startListening(onResult);
    }, 500);
  }, [orb]);

  // Handle voice result for name
  const handleVoiceNameResult = useCallback((transcript: string) => {
    setWaitingForVoice(false);
    const name = transcript.trim();
    if (name) {
      setUserName(name);
      setConfirmedName(name);
      setStep('confirm_name');
    } else {
      // Retry
      orb.speak("Non ho capito, puoi ripetere il tuo nome?");
      typeText("Non ho capito, puoi ripetere il tuo nome?", () => {
        startListeningAfterSpeak(handleVoiceNameResult);
      });
    }
  }, [orb, typeText, startListeningAfterSpeak]);

  // Handle voice confirmation
  const handleVoiceConfirmResult = useCallback((transcript: string) => {
    setWaitingForVoice(false);
    const response = transcript.toLowerCase().trim();

    // Check for positive response
    const positiveWords = ['si', 'sì', 'corretto', 'esatto', 'ok', 'okay', 'giusto', 'confermo', 'yes'];
    const negativeWords = ['no', 'sbagliato', 'errato', 'non', 'correggi', 'ripeti'];

    const isPositive = positiveWords.some(word => response.includes(word));
    const isNegative = negativeWords.some(word => response.includes(word));

    if (isPositive && !isNegative) {
      handleConfirmName(true);
    } else if (isNegative) {
      handleConfirmName(false);
    } else {
      // Ask again
      orb.speak("Scusa, non ho capito. Il nome è corretto? Rispondi sì o no.");
      typeText("Scusa, non ho capito. Il nome è corretto? Rispondi sì o no.", () => {
        startListeningAfterSpeak(handleVoiceConfirmResult);
      });
    }
  }, [orb, typeText, startListeningAfterSpeak]);

  // Initial greeting
  useEffect(() => {
    const timer = setTimeout(() => {
      orb.speak("Ciao! Sono LORENZ, il tuo assistente personale digitale.");
      typeText("Ciao! Sono LORENZ, il tuo assistente personale digitale.", () => {
        setTimeout(() => {
          setStep('ask_name');
        }, 1500);
      });
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  // Handle step changes
  useEffect(() => {
    switch (step) {
      case 'ask_name':
        orb.speak("Come ti chiami? Dimmi il tuo nome e cognome.", 'center');
        typeText("Come ti chiami? Dimmi il tuo nome e cognome.", () => {
          if (speechSupported) {
            startListeningAfterSpeak(handleVoiceNameResult);
          }
        });
        break;

      case 'confirm_name':
        orb.moveTo('left');
        orb.speak(`${confirmedName}. È corretto?`);
        typeText(`${confirmedName}. È corretto?`, () => {
          if (speechSupported) {
            startListeningAfterSpeak(handleVoiceConfirmResult);
          }
        });
        break;

      case 'searching':
        orb.think();
        orb.moveTo('center');
        typeText("Sto cercando informazioni su di te nel web...");
        break;

      case 'show_profile':
        if (profile) {
          orb.moveTo('top-left');
          orb.speak(profile.lorenz_introduction || `Piacere di conoscerti, ${profile.first_name}!`);
          typeText(profile.lorenz_introduction || `Piacere di conoscerti, ${profile.first_name}!`);
        }
        break;

      case 'disambiguation':
        orb.speak("Ho trovato più persone con questo nome. Quale sei tu? Dimmi il numero.");
        typeText("Ho trovato più persone con questo nome. Quale sei tu? Dimmi il numero.", () => {
          if (speechSupported) {
            startListeningAfterSpeak(handleVoiceDisambiguationResult);
          }
        });
        break;

      case 'complete':
        orb.success();
        orb.speak("Perfetto! Ora so chi sei. Iniziamo il tuo viaggio insieme!");
        typeText("Perfetto! Ora so chi sei. Iniziamo il tuo viaggio insieme!");
        break;
    }
  }, [step, confirmedName, profile, speechSupported]);

  // Handle name confirmation
  const handleConfirmName = async (confirmed: boolean) => {
    setWaitingForVoice(false);

    if (confirmed) {
      // Start searching
      setStep('searching');
      setIsLoading(true);

      try {
        // Confirm name with backend
        await api.post('/onboarding/identity/confirm-name', {
          full_name: confirmedName
        });

        // Discover identity
        const response = await api.post('/onboarding/identity/discover', {
          full_name: confirmedName
        });

        setProfile(response);
        setIsLoading(false);

        if (response.disambiguation_needed) {
          setStep('disambiguation');
        } else {
          setStep('show_profile');
        }
      } catch (error) {
        console.error('Error discovering identity:', error);
        setIsLoading(false);
        // Still show profile step even if discovery fails
        setProfile({
          full_name: confirmedName,
          first_name: confirmedName.split(' ')[0],
          last_name: confirmedName.split(' ').slice(1).join(' '),
          confidence_score: 0,
          disambiguation_needed: false,
          lorenz_introduction: `Piacere di conoscerti, ${confirmedName.split(' ')[0]}! Non ho trovato informazioni su di te online, ma non preoccuparti, imparerò a conoscerti piano piano.`
        });
        setStep('show_profile');
      }
    } else {
      // Ask for name again
      setUserName('');
      setStep('ask_name');
    }
  };

  // Handle voice disambiguation
  const handleVoiceDisambiguationResult = useCallback((transcript: string) => {
    setWaitingForVoice(false);
    const response = transcript.toLowerCase().trim();

    // Extract number from response
    const numbers: Record<string, number> = {
      'uno': 0, 'una': 0, '1': 0, 'primo': 0, 'prima': 0,
      'due': 1, '2': 1, 'secondo': 1, 'seconda': 1,
      'tre': 2, '3': 2, 'terzo': 2, 'terza': 2,
      'nessuno': -1, 'nessuna': -1, 'niente': -1
    };

    let selectedIndex = -2;
    for (const [word, index] of Object.entries(numbers)) {
      if (response.includes(word)) {
        selectedIndex = index;
        break;
      }
    }

    if (selectedIndex === -1) {
      // None selected
      setStep('show_profile');
    } else if (selectedIndex >= 0 && profile?.disambiguation_options && selectedIndex < profile.disambiguation_options.length) {
      handleDisambiguationSelect(selectedIndex);
    } else {
      // Retry
      orb.speak("Non ho capito, dimmi il numero dell'opzione, oppure 'nessuna'.");
      typeText("Non ho capito, dimmi il numero dell'opzione, oppure 'nessuna'.", () => {
        startListeningAfterSpeak(handleVoiceDisambiguationResult);
      });
    }
  }, [profile, orb, typeText, startListeningAfterSpeak]);

  // Handle disambiguation selection
  const handleDisambiguationSelect = async (index: number) => {
    setIsLoading(true);
    setStep('searching');

    try {
      const response = await api.post('/onboarding/identity/resolve-disambiguation', {
        selected_option: index
      });

      setProfile(response);
      setIsLoading(false);
      setStep('show_profile');
    } catch (error) {
      console.error('Error resolving disambiguation:', error);
      setIsLoading(false);
      setStep('show_profile');
    }
  };

  // Handle field correction
  const handleFieldCorrection = async (field: string, value: string) => {
    try {
      await api.post('/onboarding/identity/update-field', {
        field,
        value
      });

      // Update local profile
      if (profile) {
        setProfile({
          ...profile,
          [field]: value
        });
      }
      setEditingField(null);
      setEditValue('');
    } catch (error) {
      console.error('Error updating field:', error);
    }
  };

  // Complete onboarding
  const handleComplete = async () => {
    if (!profile) return;

    try {
      await api.post('/onboarding/identity/complete', {
        profile_data: profile,
        assistant_name: 'LORENZ'
      });

      setStep('complete');
      setTimeout(() => {
        router.push('/setup');
      }, 3000);
    } catch (error) {
      console.error('Error completing onboarding:', error);
      router.push('/setup');
    }
  };

  // Profile field display
  const ProfileField = ({
    label,
    value,
    field
  }: {
    label: string;
    value: string | number | undefined;
    field: string;
  }) => {
    if (!value) return null;

    const isEditing = editingField === field;

    return (
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between py-2 border-b border-white/10"
      >
        <span className="text-white/60 text-sm">{label}</span>
        {isEditing ? (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="bg-white/10 rounded px-2 py-1 text-white text-sm"
              autoFocus
            />
            <button
              onClick={() => handleFieldCorrection(field, editValue)}
              className="text-green-400 text-sm hover:text-green-300"
            >
              OK
            </button>
            <button
              onClick={() => { setEditingField(null); setEditValue(''); }}
              className="text-red-400 text-sm hover:text-red-300"
            >
              X
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-white font-medium">{value}</span>
            <button
              onClick={() => { setEditingField(field); setEditValue(String(value)); }}
              className="text-white/40 text-xs hover:text-white"
            >
              Correggi
            </button>
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex flex-col items-center justify-center p-8 overflow-hidden">
      {/* Stars background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              opacity: Math.random() * 0.5 + 0.2,
            }}
          />
        ))}
      </div>

      {/* Main content */}
      <div className="relative z-10 w-full max-w-4xl flex flex-col items-center">
        {/* Orb */}
        <LorenzOrb
          state={orb.state}
          position={orb.position}
          size="xl"
          text={orb.text}
          onSpeakEnd={() => orb.idle()}
          className="mb-8"
        />

        {/* Voice indicator */}
        <AnimatePresence>
          {waitingForVoice && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="mb-4 flex items-center gap-2 text-indigo-400"
            >
              <div className="w-3 h-3 bg-indigo-400 rounded-full animate-pulse" />
              <span className="text-sm">
                {orb.transcript || "In ascolto..."}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Displayed text */}
        <AnimatePresence mode="wait">
          <motion.div
            key={displayedText}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="text-center mb-8 min-h-[60px]"
          >
            <p className="text-2xl text-white font-light">{displayedText}</p>
          </motion.div>
        </AnimatePresence>

        {/* Fallback input for no speech support */}
        <AnimatePresence>
          {!speechSupported && step === 'ask_name' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-md"
            >
              <p className="text-white/60 text-sm text-center mb-4">
                Il riconoscimento vocale non è supportato. Usa la tastiera:
              </p>
              <input
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="Nome e Cognome"
                className="w-full px-6 py-4 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl text-white text-xl text-center placeholder:text-white/40 focus:outline-none focus:border-indigo-400"
                autoFocus
              />
              <button
                onClick={() => {
                  if (userName.trim()) {
                    setConfirmedName(userName.trim());
                    setStep('confirm_name');
                  }
                }}
                disabled={!userName.trim()}
                className="mt-4 w-full py-3 bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-medium rounded-xl hover:opacity-90 transition disabled:opacity-50"
              >
                Continua
              </button>
            </motion.div>
          )}

          {!speechSupported && step === 'confirm_name' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex gap-4"
            >
              <button
                onClick={() => handleConfirmName(true)}
                className="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:opacity-90 transition"
              >
                Si, corretto
              </button>
              <button
                onClick={() => handleConfirmName(false)}
                className="px-8 py-3 bg-white/10 text-white font-medium rounded-xl hover:bg-white/20 transition"
              >
                No, correggi
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Name display (when confirmed and moving orb) */}
        <AnimatePresence>
          {(step === 'confirm_name' || step === 'searching' || step === 'show_profile') && confirmedName && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="absolute top-8 right-8 text-right"
            >
              <p className="text-white/60 text-sm">Nome</p>
              <p className="text-3xl font-bold text-white">{confirmedName}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Disambiguation options */}
        <AnimatePresence>
          {step === 'disambiguation' && profile?.disambiguation_options && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-lg space-y-3 mt-4"
            >
              {profile.disambiguation_options.map((option, index) => (
                <motion.button
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleDisambiguationSelect(index)}
                  className="w-full p-4 bg-white/10 backdrop-blur-sm rounded-xl text-left hover:bg-white/20 transition"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-indigo-400 font-bold">{index + 1}.</span>
                    <div>
                      <p className="text-white">{option.description}</p>
                      {option.context && (
                        <p className="text-white/60 text-sm mt-1">{option.context}</p>
                      )}
                    </div>
                  </div>
                </motion.button>
              ))}
              <button
                onClick={() => setStep('show_profile')}
                className="w-full p-3 text-white/60 hover:text-white transition"
              >
                Nessuna di queste
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Profile card */}
        <AnimatePresence>
          {step === 'show_profile' && profile && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className="w-full max-w-lg bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 mt-8"
            >
              <h2 className="text-xl font-bold text-white mb-4">Il tuo profilo</h2>

              <div className="space-y-1">
                <ProfileField label="Nome" value={profile.full_name} field="full_name" />
                <ProfileField label="Professione" value={profile.profession} field="profession" />
                <ProfileField label="Azienda" value={profile.company} field="company" />
                <ProfileField label="Ruolo" value={profile.role} field="role" />
                <ProfileField label="Settore" value={profile.industry} field="industry" />
                <ProfileField label="Luogo" value={profile.location} field="location" />
                <ProfileField label="Nazionalita" value={profile.nationality} field="nationality" />
                <ProfileField label="Eta" value={profile.age} field="age" />
                <ProfileField label="Stato civile" value={profile.marital_status} field="marital_status" />
                {profile.has_children && (
                  <ProfileField label="Figli" value={profile.children_count || 'Si'} field="children_count" />
                )}
                <ProfileField label="Formazione" value={profile.education} field="education" />
              </div>

              {profile.notable_achievements && profile.notable_achievements.length > 0 && (
                <div className="mt-4">
                  <p className="text-white/60 text-sm mb-2">Traguardi notevoli</p>
                  <ul className="space-y-1">
                    {profile.notable_achievements.map((achievement, i) => (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + i * 0.1 }}
                        className="text-white text-sm flex items-start gap-2"
                      >
                        <span className="text-indigo-400">•</span>
                        {achievement}
                      </motion.li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confidence indicator */}
              <div className="mt-6 pt-4 border-t border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white/60 text-sm">Accuratezza informazioni</span>
                  <span className="text-white text-sm">{Math.round(profile.confidence_score * 100)}%</span>
                </div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${profile.confidence_score * 100}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500"
                  />
                </div>
              </div>

              {/* Complete button */}
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                onClick={handleComplete}
                className="mt-6 w-full py-3 bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-medium rounded-xl hover:opacity-90 transition"
              >
                Tutto corretto, prosegui
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-8"
          >
            <div className="flex items-center gap-2 text-white/60">
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
