'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

interface AudioAnalyzerOptions {
  fftSize?: number;
  smoothingTimeConstant?: number;
  minDecibels?: number;
  maxDecibels?: number;
}

interface AudioAnalyzerState {
  isListening: boolean;
  inputVolume: number;
  outputVolume: number;
  error: string | null;
}

interface AudioAnalyzerReturn extends AudioAnalyzerState {
  startListening: () => Promise<void>;
  stopListening: () => void;
  analyzeAudioElement: (audioElement: HTMLAudioElement) => void;
  disconnectAudioElement: () => void;
}

const defaultOptions: AudioAnalyzerOptions = {
  fftSize: 256,
  smoothingTimeConstant: 0.5, // Lower for more responsive
  minDecibels: -85,
  maxDecibels: -10
};

export function useAudioAnalyzer(options: AudioAnalyzerOptions = {}): AudioAnalyzerReturn {
  const opts = { ...defaultOptions, ...options };

  const [state, setState] = useState<AudioAnalyzerState>({
    isListening: false,
    inputVolume: 0,
    outputVolume: 0,
    error: null
  });

  // Refs for audio context and analyzers
  const audioContextRef = useRef<AudioContext | null>(null);
  const inputAnalyzerRef = useRef<AnalyserNode | null>(null);
  const outputAnalyzerRef = useRef<AnalyserNode | null>(null);
  const inputStreamRef = useRef<MediaStream | null>(null);
  const outputSourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const inputDataArrayRef = useRef<Uint8Array | null>(null);
  const outputDataArrayRef = useRef<Uint8Array | null>(null);

  // Initialize audio context
  const initAudioContext = useCallback(async () => {
    if (!audioContextRef.current) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContextClass();
    }

    // Always resume the context (required for user gesture)
    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }

    return audioContextRef.current;
  }, []);

  // Calculate volume from frequency data (0-1)
  const calculateVolume = useCallback((analyzer: AnalyserNode, dataArray: Uint8Array): number => {
    analyzer.getByteFrequencyData(dataArray as any);

    let sum = 0;
    let count = 0;

    // Focus on voice frequencies (roughly 85-255 Hz range in the array)
    const startBin = Math.floor(dataArray.length * 0.1);
    const endBin = Math.floor(dataArray.length * 0.7);

    for (let i = startBin; i < endBin; i++) {
      sum += dataArray[i];
      count++;
    }

    if (count === 0) return 0;

    const average = sum / count;
    // Normalize to 0-1 range with higher amplification for voice
    const normalized = Math.min(1, (average / 128) * 2.0);

    return normalized;
  }, []);

  // Animation loop for continuous volume analysis
  const updateVolumes = useCallback(() => {
    let inputVol = 0;
    let outputVol = 0;

    if (inputAnalyzerRef.current && inputDataArrayRef.current) {
      inputVol = calculateVolume(inputAnalyzerRef.current, inputDataArrayRef.current);
    }

    if (outputAnalyzerRef.current && outputDataArrayRef.current) {
      outputVol = calculateVolume(outputAnalyzerRef.current, outputDataArrayRef.current);
    }

    setState(prev => ({
      ...prev,
      inputVolume: inputVol,
      outputVolume: outputVol
    }));

    animationFrameRef.current = requestAnimationFrame(updateVolumes);
  }, [calculateVolume]);

  // Start microphone listening
  const startListening = useCallback(async () => {
    try {
      // Check if getUserMedia is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Il browser non supporta l\'accesso al microfono');
      }

      const audioContext = await initAudioContext();

      // Get microphone stream with specific constraints
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false, // Disable for better voice detection
          noiseSuppression: false, // Disable for raw audio
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 44100,
        }
      });

      inputStreamRef.current = stream;

      // Create analyzer for input with voice-optimized settings
      const inputAnalyzer = audioContext.createAnalyser();
      inputAnalyzer.fftSize = opts.fftSize!;
      inputAnalyzer.smoothingTimeConstant = opts.smoothingTimeConstant!;
      inputAnalyzer.minDecibels = opts.minDecibels!;
      inputAnalyzer.maxDecibels = opts.maxDecibels!;

      inputAnalyzerRef.current = inputAnalyzer;
      inputDataArrayRef.current = new Uint8Array(inputAnalyzer.frequencyBinCount);

      // Connect microphone to analyzer
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(inputAnalyzer);

      // Note: We don't connect to destination to avoid feedback loop

      setState(prev => ({
        ...prev,
        isListening: true,
        error: null
      }));

      // Start animation loop
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      updateVolumes();

    } catch (err) {
      let errorMessage = 'Errore nell\'accesso al microfono';

      if (err instanceof Error) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          errorMessage = 'Permesso microfono negato. Concedi l\'accesso nelle impostazioni del browser.';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          errorMessage = 'Nessun microfono trovato. Collega un microfono e riprova.';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          errorMessage = 'Il microfono è in uso da un\'altra applicazione.';
        } else {
          errorMessage = err.message;
        }
      }

      console.error('Audio error:', err);

      setState(prev => ({
        ...prev,
        isListening: false,
        error: errorMessage
      }));
    }
  }, [initAudioContext, opts, updateVolumes]);

  // Stop microphone listening
  const stopListening = useCallback(() => {
    // Stop microphone stream
    if (inputStreamRef.current) {
      inputStreamRef.current.getTracks().forEach(track => track.stop());
      inputStreamRef.current = null;
    }

    // Disconnect input analyzer
    inputAnalyzerRef.current = null;
    inputDataArrayRef.current = null;

    // Cancel animation frame if no output is connected
    if (!outputAnalyzerRef.current && animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isListening: false,
      inputVolume: 0
    }));
  }, []);

  // Connect an audio element for output analysis
  const analyzeAudioElement = useCallback(async (audioElement: HTMLAudioElement) => {
    try {
      const audioContext = await initAudioContext();

      // Create analyzer for output
      const outputAnalyzer = audioContext.createAnalyser();
      outputAnalyzer.fftSize = opts.fftSize!;
      outputAnalyzer.smoothingTimeConstant = opts.smoothingTimeConstant!;
      outputAnalyzer.minDecibels = opts.minDecibels!;
      outputAnalyzer.maxDecibels = opts.maxDecibels!;

      outputAnalyzerRef.current = outputAnalyzer;
      outputDataArrayRef.current = new Uint8Array(outputAnalyzer.frequencyBinCount);

      // Connect audio element to analyzer
      // Check if source already exists
      if (!outputSourceRef.current) {
        const source = audioContext.createMediaElementSource(audioElement);
        outputSourceRef.current = source;
        source.connect(outputAnalyzer);
        outputAnalyzer.connect(audioContext.destination);
      }

      // Start animation loop if not already running
      if (!animationFrameRef.current) {
        updateVolumes();
      }
    } catch (err) {
      console.error('Failed to analyze audio element:', err);
    }
  }, [initAudioContext, opts, updateVolumes]);

  // Disconnect audio element analysis
  const disconnectAudioElement = useCallback(() => {
    outputAnalyzerRef.current = null;
    outputDataArrayRef.current = null;
    // Don't disconnect the source as it can't be reconnected

    // Cancel animation frame if no input is connected
    if (!inputAnalyzerRef.current && animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setState(prev => ({
      ...prev,
      outputVolume: 0
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      if (inputStreamRef.current) {
        inputStreamRef.current.getTracks().forEach(track => track.stop());
      }

      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []);

  return {
    ...state,
    startListening,
    stopListening,
    analyzeAudioElement,
    disconnectAudioElement
  };
}

// Simulated audio hook for demo purposes
export function useSimulatedAudio() {
  const [inputVolume, setInputVolume] = useState(0);
  const [outputVolume, setOutputVolume] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);
  const frameRef = useRef<number | null>(null);

  const startSimulation = useCallback((type: 'input' | 'output' | 'both') => {
    setIsSimulating(true);

    const animate = () => {
      const time = Date.now() / 1000;

      if (type === 'input' || type === 'both') {
        // Simulate speech-like patterns
        const baseInput = Math.sin(time * 8) * 0.3 + 0.3;
        const noise = Math.random() * 0.2;
        const envelope = Math.sin(time * 2) * 0.5 + 0.5;
        setInputVolume(Math.max(0, Math.min(1, baseInput * envelope + noise)));
      }

      if (type === 'output' || type === 'both') {
        // Simulate TTS-like patterns
        const baseOutput = Math.sin(time * 6) * 0.4 + 0.4;
        const variation = Math.sin(time * 15) * 0.1;
        const pause = Math.sin(time * 0.5) > 0.3 ? 1 : 0.1;
        setOutputVolume(Math.max(0, Math.min(1, (baseOutput + variation) * pause)));
      }

      frameRef.current = requestAnimationFrame(animate);
    };

    animate();
  }, []);

  const stopSimulation = useCallback(() => {
    setIsSimulating(false);
    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    setInputVolume(0);
    setOutputVolume(0);
  }, []);

  useEffect(() => {
    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, []);

  return {
    inputVolume,
    outputVolume,
    isSimulating,
    startSimulation,
    stopSimulation
  };
}

export default useAudioAnalyzer;
