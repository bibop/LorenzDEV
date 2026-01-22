'use client';

import { useState, useEffect, useRef } from 'react';
import { VoiceOrb } from '@/components/voice';
import type { OrbState } from '@/components/voice';
import { Mic, MicOff, Volume2, VolumeX, Play, Square, AlertCircle } from 'lucide-react';

// Direct microphone hook with debug
function useMicrophoneDebug() {
  const [isListening, setIsListening] = useState(false);
  const [volume, setVolume] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [debug, setDebug] = useState<string[]>([]);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationRef = useRef<number | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);

  const addDebug = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setDebug(prev => [...prev.slice(-10), `[${timestamp}] ${msg}`]);
  };

  const startListening = async () => {
    try {
      setError(null);
      addDebug('Starting microphone...');

      // Check browser support
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser does not support getUserMedia');
      }
      addDebug('getUserMedia is supported');

      // Create AudioContext
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass();
      audioContextRef.current = audioContext;
      addDebug(`AudioContext created, state: ${audioContext.state}`);

      // Resume if suspended
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
        addDebug(`AudioContext resumed, state: ${audioContext.state}`);
      }

      // Get microphone
      addDebug('Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: true,
        }
      });
      streamRef.current = stream;
      addDebug(`Got stream with ${stream.getAudioTracks().length} audio tracks`);

      const track = stream.getAudioTracks()[0];
      addDebug(`Track: ${track.label}, enabled: ${track.enabled}, muted: ${track.muted}`);

      // Create analyser
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.3;
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;
      analyserRef.current = analyser;
      addDebug(`Analyser created, frequencyBinCount: ${analyser.frequencyBinCount}`);

      // Connect
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      addDebug('Source connected to analyser');

      // Create data array
      dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);

      setIsListening(true);
      addDebug('Listening started!');

      // Start analysis loop
      const analyze = () => {
        if (!analyserRef.current || !dataArrayRef.current) return;

        analyserRef.current.getByteFrequencyData(dataArrayRef.current);

        // Calculate volume
        let sum = 0;
        for (let i = 0; i < dataArrayRef.current.length; i++) {
          sum += dataArrayRef.current[i];
        }
        const avg = sum / dataArrayRef.current.length;
        const normalizedVolume = Math.min(1, avg / 128);

        setVolume(normalizedVolume);

        animationRef.current = requestAnimationFrame(analyze);
      };

      analyze();

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      addDebug(`ERROR: ${errorMsg}`);
      console.error('Microphone error:', err);
    }
  };

  const stopListening = () => {
    addDebug('Stopping microphone...');

    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        addDebug(`Track stopped: ${track.label}`);
      });
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
      addDebug('AudioContext closed');
    }

    analyserRef.current = null;
    dataArrayRef.current = null;
    setIsListening(false);
    setVolume(0);
    addDebug('Microphone stopped');
  };

  useEffect(() => {
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, []);

  return { isListening, volume, error, debug, startListening, stopListening };
}

// Simulated audio
function useSimulatedAudio() {
  const [volume, setVolume] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);
  const frameRef = useRef<number | null>(null);

  const startSimulation = (type: 'input' | 'output') => {
    setIsSimulating(true);
    const animate = () => {
      const time = Date.now() / 1000;
      const base = Math.sin(time * 8) * 0.3 + 0.3;
      const noise = Math.random() * 0.2;
      const envelope = Math.sin(time * 2) * 0.5 + 0.5;
      setVolume(Math.max(0, Math.min(1, base * envelope + noise)));
      frameRef.current = requestAnimationFrame(animate);
    };
    animate();
  };

  const stopSimulation = () => {
    setIsSimulating(false);
    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    setVolume(0);
  };

  useEffect(() => {
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return { volume, isSimulating, startSimulation, stopSimulation };
}

export default function VoiceOrbDemo() {
  const [state, setState] = useState<OrbState>('idle');
  const [useRealMic, setUseRealMic] = useState(false);

  const mic = useMicrophoneDebug();
  const sim = useSimulatedAudio();

  const inputVolume = useRealMic ? mic.volume : sim.volume;

  const handleToggleMic = async () => {
    if (mic.isListening) {
      mic.stopListening();
      setState('idle');
      setUseRealMic(false);
    } else {
      setUseRealMic(true);
      await mic.startListening();
      setState('listening');
    }
  };

  const handleSimulate = () => {
    if (sim.isSimulating) {
      sim.stopSimulation();
      setState('idle');
      setUseRealMic(false);
    } else {
      setUseRealMic(false);
      sim.startSimulation('input');
      setState('listening');
    }
  };

  // Color presets
  const colorPresets = {
    pastel: {
      primary: '#C4B5FD',
      secondary: '#93C5FD',
      glow: '#A5B4FC'
    },
    emerald: {
      primary: '#6EE7B7',
      secondary: '#34D399',
      glow: '#A7F3D0'
    },
    rose: {
      primary: '#FDA4AF',
      secondary: '#FB7185',
      glow: '#FECDD3'
    },
    amber: {
      primary: '#FCD34D',
      secondary: '#FBBF24',
      glow: '#FDE68A'
    }
  };

  const [selectedColors, setSelectedColors] = useState<keyof typeof colorPresets>('pastel');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold text-white mb-2">LORENZ Voice Orb</h1>
      <p className="text-slate-400 mb-8">Ethereal 3D voice visualization with glow</p>

      {/* Orb Container */}
      <div className="w-80 h-80 mb-8">
        <VoiceOrb
          state={state}
          inputVolume={inputVolume}
          outputVolume={0}
          colors={colorPresets[selectedColors]}
          size={1.2}
          className="w-full h-full"
        />
      </div>

      {/* Volume Indicator */}
      <div className="mb-6 text-center">
        <div className="text-sm text-slate-400 mb-2">
          Volume: {(inputVolume * 100).toFixed(0)}%
          {mic.isListening && ' (Real Mic)'}
          {sim.isSimulating && ' (Simulated)'}
        </div>
        <div className="w-48 h-3 bg-slate-700 rounded-full overflow-hidden mx-auto">
          <div
            className="h-full bg-gradient-to-r from-violet-500 to-purple-400 transition-all duration-75"
            style={{ width: `${inputVolume * 100}%` }}
          />
        </div>
      </div>

      {/* State Selector */}
      <div className="flex gap-2 mb-6">
        {(['idle', 'listening', 'speaking', 'thinking'] as OrbState[]).map(s => (
          <button
            key={s}
            onClick={() => setState(s)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              state === s
                ? 'bg-violet-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Color Presets */}
      <div className="flex gap-3 mb-6">
        {Object.entries(colorPresets).map(([name, colors]) => (
          <button
            key={name}
            onClick={() => setSelectedColors(name as keyof typeof colorPresets)}
            className={`w-10 h-10 rounded-full border-2 transition ${
              selectedColors === name ? 'border-white scale-110' : 'border-transparent'
            }`}
            style={{ background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})` }}
            title={name}
          />
        ))}
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 justify-center mb-6">
        <button
          onClick={handleToggleMic}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition ${
            mic.isListening
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-emerald-600 text-white hover:bg-emerald-700'
          }`}
        >
          {mic.isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          {mic.isListening ? 'Stop Mic' : 'Use Real Mic'}
        </button>

        <button
          onClick={handleSimulate}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition ${
            sim.isSimulating
              ? 'bg-orange-600 text-white hover:bg-orange-700'
              : 'bg-slate-700 text-white hover:bg-slate-600'
          }`}
        >
          {sim.isSimulating ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          {sim.isSimulating ? 'Stop Simulation' : 'Simulate Voice'}
        </button>
      </div>

      {/* Error display */}
      {mic.error && (
        <div className="mb-4 px-4 py-3 bg-red-900/50 border border-red-500 rounded-lg text-red-200 text-sm flex items-center gap-2 max-w-md">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{mic.error}</span>
        </div>
      )}

      {/* Debug Log */}
      <div className="w-full max-w-lg bg-slate-800/80 rounded-lg p-4 text-xs font-mono">
        <div className="text-slate-400 mb-2 font-bold">Debug Log:</div>
        <div className="space-y-1 max-h-40 overflow-y-auto">
          {mic.debug.length === 0 ? (
            <div className="text-slate-500">Click "Use Real Mic" to start...</div>
          ) : (
            mic.debug.map((log, i) => (
              <div key={i} className={`${log.includes('ERROR') ? 'text-red-400' : 'text-green-400'}`}>
                {log}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Info */}
      <div className="mt-6 text-center text-slate-500 text-sm max-w-md">
        <p>
          Click &quot;Use Real Mic&quot; and allow microphone access.
          The orb will react to your voice with a soft, ethereal glow effect.
        </p>
      </div>
    </div>
  );
}
