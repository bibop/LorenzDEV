'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type OrbState = 'idle' | 'speaking' | 'listening' | 'thinking' | 'success' | 'error';
type OrbPosition = 'center' | 'left' | 'right' | 'top-left';

interface LorenzOrbProps {
  state?: OrbState;
  position?: OrbPosition;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  onSpeakEnd?: () => void;
  onSpeechResult?: (transcript: string) => void;
  autoSpeak?: boolean;
  className?: string;
}

// Speech Recognition types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

// Posizioni dell'orb
const positionVariants = {
  center: { x: 0, y: 0, scale: 1 },
  left: { x: -200, y: 0, scale: 0.8 },
  right: { x: 200, y: 0, scale: 0.8 },
  'top-left': { x: -300, y: -150, scale: 0.6 },
};

// Dimensioni dell'orb
const sizeMap = {
  sm: 80,
  md: 120,
  lg: 180,
  xl: 240,
};

export default function LorenzOrb({
  state = 'idle',
  position = 'center',
  size = 'lg',
  text,
  onSpeakEnd,
  autoSpeak = true,
  className = '',
}: LorenzOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const orbSize = sizeMap[size];

  // Inizializza Web Speech API
  useEffect(() => {
    if (typeof window !== 'undefined') {
      synthRef.current = window.speechSynthesis;
    }
    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Funzione per far parlare l'orb
  const speak = useCallback((message: string) => {
    if (!synthRef.current || !message) return;

    // Cancella eventuali speech in corso
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = 'it-IT';
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Cerca una voce italiana
    const voices = synthRef.current.getVoices();
    const italianVoice = voices.find(v => v.lang.startsWith('it')) || voices[0];
    if (italianVoice) {
      utterance.voice = italianVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      onSpeakEnd?.();
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      onSpeakEnd?.();
    };

    synthRef.current.speak(utterance);
  }, [onSpeakEnd]);

  // Auto-speak quando il testo cambia
  useEffect(() => {
    if (autoSpeak && text && state === 'speaking') {
      // Attendi che le voci siano caricate
      if (synthRef.current?.getVoices().length === 0) {
        synthRef.current.addEventListener('voiceschanged', () => speak(text), { once: true });
      } else {
        speak(text);
      }
    }
  }, [text, state, autoSpeak, speak]);

  // Animazione Canvas dell'Orb
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = orbSize * dpr;
    canvas.height = orbSize * dpr;
    ctx.scale(dpr, dpr);

    let time = 0;
    const centerX = orbSize / 2;
    const centerY = orbSize / 2;
    const baseRadius = orbSize * 0.35;

    const animate = () => {
      ctx.clearRect(0, 0, orbSize, orbSize);
      time += 0.02;

      // Determina l'intensità dell'animazione basata sullo stato
      let pulseIntensity = 0.05;
      let glowIntensity = 0.5;
      let colorShift = 0;

      switch (state) {
        case 'speaking':
          pulseIntensity = 0.15 + (isSpeaking ? Math.sin(time * 8) * 0.1 : 0);
          glowIntensity = 0.8;
          colorShift = Math.sin(time * 3) * 20;
          break;
        case 'listening':
          pulseIntensity = 0.1 + Math.sin(time * 4) * 0.05;
          glowIntensity = 0.7;
          colorShift = Math.sin(time * 2) * 10;
          break;
        case 'thinking':
          pulseIntensity = 0.08;
          glowIntensity = 0.6;
          colorShift = time * 50;
          break;
        case 'success':
          pulseIntensity = 0.12;
          glowIntensity = 0.9;
          colorShift = 120; // Verde
          break;
        case 'error':
          pulseIntensity = 0.15;
          glowIntensity = 0.8;
          colorShift = 0; // Rosso
          break;
        default:
          pulseIntensity = 0.05 + Math.sin(time) * 0.02;
          glowIntensity = 0.5;
      }

      const currentRadius = baseRadius * (1 + Math.sin(time * 2) * pulseIntensity);

      // Glow esterno
      const gradient = ctx.createRadialGradient(
        centerX, centerY, currentRadius * 0.5,
        centerX, centerY, currentRadius * 1.5
      );

      const hue = (240 + colorShift) % 360; // Blu di base con shift
      gradient.addColorStop(0, `hsla(${hue}, 80%, 60%, ${glowIntensity})`);
      gradient.addColorStop(0.5, `hsla(${hue + 30}, 70%, 50%, ${glowIntensity * 0.5})`);
      gradient.addColorStop(1, 'hsla(260, 80%, 40%, 0)');

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentRadius * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // Orb principale con gradiente interno
      const innerGradient = ctx.createRadialGradient(
        centerX - currentRadius * 0.3,
        centerY - currentRadius * 0.3,
        0,
        centerX,
        centerY,
        currentRadius
      );

      innerGradient.addColorStop(0, `hsla(${hue}, 90%, 80%, 1)`);
      innerGradient.addColorStop(0.4, `hsla(${hue + 20}, 85%, 60%, 1)`);
      innerGradient.addColorStop(0.8, `hsla(${hue + 40}, 80%, 45%, 1)`);
      innerGradient.addColorStop(1, `hsla(${hue + 60}, 75%, 30%, 1)`);

      ctx.fillStyle = innerGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentRadius, 0, Math.PI * 2);
      ctx.fill();

      // Anelli rotanti per stato "thinking"
      if (state === 'thinking') {
        ctx.strokeStyle = `hsla(${hue}, 70%, 70%, 0.4)`;
        ctx.lineWidth = 2;
        for (let i = 0; i < 3; i++) {
          ctx.beginPath();
          ctx.arc(
            centerX,
            centerY,
            currentRadius * (1.2 + i * 0.15),
            time + i * (Math.PI / 3),
            time + i * (Math.PI / 3) + Math.PI / 2
          );
          ctx.stroke();
        }
      }

      // Particelle per stato "speaking"
      if (state === 'speaking' && isSpeaking) {
        for (let i = 0; i < 8; i++) {
          const angle = (i / 8) * Math.PI * 2 + time * 2;
          const dist = currentRadius * (1.2 + Math.sin(time * 4 + i) * 0.3);
          const x = centerX + Math.cos(angle) * dist;
          const y = centerY + Math.sin(angle) * dist;
          const size = 3 + Math.sin(time * 4 + i) * 2;

          ctx.fillStyle = `hsla(${hue + i * 20}, 80%, 70%, 0.6)`;
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Highlight
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.beginPath();
      ctx.ellipse(
        centerX - currentRadius * 0.2,
        centerY - currentRadius * 0.3,
        currentRadius * 0.25,
        currentRadius * 0.15,
        -Math.PI / 4,
        0,
        Math.PI * 2
      );
      ctx.fill();

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [state, isSpeaking, orbSize]);

  // Get position variant values
  const posVariant = positionVariants[position];

  return (
    <motion.div
      className={`relative flex items-center justify-center ${className}`}
      initial={{ opacity: 0, scale: 0.5, x: 0, y: 0 }}
      animate={{
        opacity: 1,
        x: posVariant.x,
        y: posVariant.y,
        scale: posVariant.scale,
      }}
      transition={{
        type: 'spring',
        stiffness: 100,
        damping: 20,
        duration: 0.8,
      }}
    >
      {/* Canvas dell'Orb */}
      <canvas
        ref={canvasRef}
        style={{
          width: orbSize,
          height: orbSize,
        }}
        className="drop-shadow-2xl"
      />

      {/* Indicatore di stato */}
      <AnimatePresence>
        {state === 'listening' && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            className="absolute -bottom-8 flex items-center gap-1"
          >
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-green-400">In ascolto...</span>
          </motion.div>
        )}
        {state === 'thinking' && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            className="absolute -bottom-8 flex items-center gap-1"
          >
            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-spin" />
            <span className="text-xs text-indigo-400">Sto pensando...</span>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Hook per controllare l'Orb con Speech Recognition
export function useLorenzOrb() {
  const [state, setState] = useState<OrbState>('idle');
  const [position, setPosition] = useState<OrbPosition>('center');
  const [text, setText] = useState<string>('');
  const [transcript, setTranscript] = useState<string>('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const onSpeechResultRef = useRef<((transcript: string) => void) | null>(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognitionAPI) {
        const recognition = new SpeechRecognitionAPI();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'it-IT';

        recognition.onstart = () => {
          setIsListening(true);
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              finalTranscript += result[0].transcript;
            } else {
              interimTranscript += result[0].transcript;
            }
          }

          setTranscript(finalTranscript || interimTranscript);

          if (finalTranscript && onSpeechResultRef.current) {
            onSpeechResultRef.current(finalTranscript);
          }
        };

        recognition.onerror = (event: Event) => {
          console.error('Speech recognition error:', event);
          setIsListening(false);
          setState('idle');
        };

        recognition.onend = () => {
          setIsListening(false);
          if (state === 'listening') {
            setState('idle');
          }
        };

        recognitionRef.current = recognition;
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [state]);

  const speak = useCallback((message: string, moveToPosition?: OrbPosition) => {
    setText(message);
    setState('speaking');
    if (moveToPosition) {
      setPosition(moveToPosition);
    }
  }, []);

  const startListening = useCallback((onResult?: (transcript: string) => void) => {
    if (recognitionRef.current && !isListening) {
      onSpeechResultRef.current = onResult || null;
      setTranscript('');
      setState('listening');
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
    }
  }, [isListening]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, [isListening]);

  const listen = useCallback(() => {
    setState('listening');
  }, []);

  const think = useCallback(() => {
    setState('thinking');
  }, []);

  const success = useCallback(() => {
    setState('success');
  }, []);

  const error = useCallback(() => {
    setState('error');
  }, []);

  const idle = useCallback(() => {
    setState('idle');
    setText('');
    setTranscript('');
  }, []);

  const moveTo = useCallback((pos: OrbPosition) => {
    setPosition(pos);
  }, []);

  return {
    state,
    position,
    text,
    transcript,
    isListening,
    speak,
    startListening,
    stopListening,
    listen,
    think,
    success,
    error,
    idle,
    moveTo,
  };
}
