'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api, SetupStep, SetupProgress } from '@/lib/api';
import {
  Sparkles,
  Mail,
  Calendar,
  Cloud,
  Users,
  FileText,
  Brain,
  CheckCircle2,
  Circle,
  Loader2,
  SkipForward,
  ChevronRight,
  AlertCircle,
  Folder,
  Linkedin,
  Twitter,
  Facebook,
  HardDrive,
} from 'lucide-react';

// Icons for providers
const ProviderIcons: Record<string, React.ReactNode> = {
  google: (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  ),
  microsoft: (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path fill="#F25022" d="M1 1h10v10H1z"/>
      <path fill="#00A4EF" d="M1 13h10v10H1z"/>
      <path fill="#7FBA00" d="M13 1h10v10H13z"/>
      <path fill="#FFB900" d="M13 13h10v10H13z"/>
    </svg>
  ),
  dropbox: (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#0061FF">
      <path d="M6 2L0 6l6 4-6 4 6 4 6-4-6-4 6-4-6-4zm12 0l-6 4 6 4-6 4 6 4 6-4-6-4 6-4-6-4zM6 18l6 4 6-4-6-4-6 4z"/>
    </svg>
  ),
  linkedin: <Linkedin className="w-5 h-5 text-[#0A66C2]" />,
  twitter: <Twitter className="w-5 h-5 text-[#1DA1F2]" />,
  meta: <Facebook className="w-5 h-5 text-[#1877F2]" />,
};

// Phase icons
const PhaseIcons: Record<string, React.ReactNode> = {
  detecting_local: <Folder className="w-5 h-5" />,
  connecting_email: <Mail className="w-5 h-5" />,
  connecting_calendar: <Calendar className="w-5 h-5" />,
  discovering_cloud: <Cloud className="w-5 h-5" />,
  connecting_social: <Users className="w-5 h-5" />,
  indexing_documents: <FileText className="w-5 h-5" />,
  building_profile: <Brain className="w-5 h-5" />,
};

interface SetupWizardProps {
  onComplete: () => void;
  assistantName?: string;
}

export default function SetupWizard({ onComplete, assistantName = 'LORENZ' }: SetupWizardProps) {
  const router = useRouter();
  const [progress, setProgress] = useState<SetupProgress | null>(null);
  const [currentStep, setCurrentStep] = useState<SetupStep | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systemInfo, setSystemInfo] = useState<{
    platform?: string;
    email_clients?: string[];
    calendar_sources?: string[];
  }>({});

  // Initialize setup
  useEffect(() => {
    const initSetup = async () => {
      try {
        setIsLoading(true);
        const result = await api.startAutoSetup();
        setProgress(result.progress);
        setCurrentStep(result.next_step);

        // Quick scan for system info
        try {
          const scanResult = await api.quickSystemScan();
          setSystemInfo({
            platform: scanResult.platform,
            email_clients: scanResult.email_clients_detected,
            calendar_sources: scanResult.calendar_sources_detected,
          });
        } catch {
          // Non-critical, continue without system info
        }
      } catch (err: any) {
        setError(err.message || 'Failed to start setup');
      } finally {
        setIsLoading(false);
      }
    };

    initSetup();
  }, []);

  // Execute a step
  const executeStep = useCallback(async (stepId: string, oauthTokens?: Record<string, string>) => {
    if (!progress) return;

    setIsExecuting(true);
    setError(null);

    try {
      const result = await api.executeSetupStep(stepId, oauthTokens);
      setProgress(result.progress);
      setCurrentStep(result.next_step);
    } catch (err: any) {
      setError(err.message || 'Step execution failed');
    } finally {
      setIsExecuting(false);
    }
  }, [progress]);

  // Skip a step
  const skipStep = useCallback(async (stepId: string) => {
    if (!progress) return;

    try {
      const result = await api.skipSetupStep(stepId);
      setProgress(result.progress);
      setCurrentStep(result.next_step);
    } catch (err: any) {
      setError(err.message || 'Failed to skip step');
    }
  }, [progress]);

  // Complete setup
  const completeSetup = useCallback(async () => {
    try {
      await api.completeAutoSetup();
      onComplete();
    } catch (err: any) {
      setError(err.message || 'Failed to complete setup');
    }
  }, [onComplete]);

  // Handle OAuth callback (simplified - in production, use proper OAuth flow)
  const handleOAuthConnect = useCallback(async (step: SetupStep) => {
    if (!step.oauth_provider) return;

    // Open OAuth popup
    const width = 600;
    const height = 700;
    const left = (window.innerWidth - width) / 2;
    const top = (window.innerHeight - height) / 2;

    const oauthUrl = api.getOAuthUrl(step.oauth_provider);
    const popup = window.open(
      oauthUrl,
      'oauth',
      `width=${width},height=${height},left=${left},top=${top}`
    );

    // Listen for OAuth completion (simplified)
    // In production, use proper OAuth callback handling
    const checkPopup = setInterval(() => {
      if (popup?.closed) {
        clearInterval(checkPopup);
        // For demo, execute step without tokens
        // In production, you'd get tokens from the callback
        executeStep(step.id, { access_token: 'demo_token' });
      }
    }, 500);
  }, [executeStep]);

  // Render step card
  const renderStepCard = (step: SetupStep) => {
    const isActive = currentStep?.id === step.id;
    const isCompleted = step.status === 'completed';
    const isSkipped = step.status === 'skipped';
    const isFailed = step.status === 'failed';

    return (
      <div
        key={step.id}
        className={`
          relative p-4 rounded-xl border transition-all duration-300
          ${isActive ? 'border-primary bg-primary/5 ring-2 ring-primary/20' : ''}
          ${isCompleted ? 'border-green-500/30 bg-green-500/5' : ''}
          ${isSkipped ? 'border-muted bg-muted/30 opacity-60' : ''}
          ${isFailed ? 'border-red-500/30 bg-red-500/5' : ''}
          ${!isActive && !isCompleted && !isSkipped && !isFailed ? 'border-border bg-card' : ''}
        `}
      >
        <div className="flex items-start gap-3">
          {/* Status Icon */}
          <div className={`
            w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
            ${isCompleted ? 'bg-green-500 text-white' : ''}
            ${isActive ? 'bg-primary text-white' : ''}
            ${isSkipped ? 'bg-muted text-muted-foreground' : ''}
            ${isFailed ? 'bg-red-500 text-white' : ''}
            ${!isActive && !isCompleted && !isSkipped && !isFailed ? 'bg-muted text-muted-foreground' : ''}
          `}>
            {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : null}
            {isActive && isExecuting ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
            {isActive && !isExecuting ? PhaseIcons[step.phase] || <Circle className="w-5 h-5" /> : null}
            {isFailed ? <AlertCircle className="w-5 h-5" /> : null}
            {!isActive && !isCompleted && !isFailed ? <Circle className="w-4 h-4" /> : null}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-sm">{step.title}</h3>
              {step.priority === 'required' && (
                <span className="text-[10px] px-1.5 py-0.5 bg-primary/10 text-primary rounded">Required</span>
              )}
              {step.requires_oauth && step.oauth_provider && (
                <span className="flex items-center gap-1">
                  {ProviderIcons[step.oauth_provider]}
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{step.description}</p>

            {/* Error */}
            {isFailed && step.error && (
              <p className="text-xs text-red-500 mt-1">{step.error}</p>
            )}

            {/* Result summary */}
            {isCompleted && step.result && (
              <div className="text-xs text-green-600 mt-1">
                {step.id === 'local_scan' && step.result.files_found && (
                  <span>Found {step.result.files_found} files</span>
                )}
                {step.id.startsWith('cloud_') && step.result.files_found && (
                  <span>Found {step.result.files_found} files</span>
                )}
                {step.id.startsWith('social_') && step.result.profile && (
                  <span>Connected as {step.result.profile.name}</span>
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          {isActive && !isExecuting && (
            <div className="flex items-center gap-2 flex-shrink-0">
              {step.priority !== 'required' && (
                <button
                  onClick={() => skipStep(step.id)}
                  className="text-xs text-muted-foreground hover:text-foreground transition"
                >
                  <SkipForward className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => step.requires_oauth ? handleOAuthConnect(step) : executeStep(step.id)}
                className="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded-lg hover:bg-primary/90 transition flex items-center gap-1"
              >
                {step.requires_oauth ? 'Connect' : 'Start'}
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Preparing your setup...</p>
      </div>
    );
  }

  // Error state
  if (error && !progress) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Setup Error</h2>
        <p className="text-muted-foreground mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary text-white rounded-lg"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Group steps by phase
  const stepsByPhase: Record<string, SetupStep[]> = {};
  progress?.steps.forEach(step => {
    if (!stepsByPhase[step.phase]) {
      stepsByPhase[step.phase] = [];
    }
    stepsByPhase[step.phase].push(step);
  });

  const phases = [
    { key: 'detecting_local', title: 'Local Files', icon: <HardDrive className="w-4 h-4" /> },
    { key: 'connecting_email', title: 'Email', icon: <Mail className="w-4 h-4" /> },
    { key: 'connecting_calendar', title: 'Calendar', icon: <Calendar className="w-4 h-4" /> },
    { key: 'discovering_cloud', title: 'Cloud Storage', icon: <Cloud className="w-4 h-4" /> },
    { key: 'connecting_social', title: 'Social', icon: <Users className="w-4 h-4" /> },
    { key: 'indexing_documents', title: 'Documents', icon: <FileText className="w-4 h-4" /> },
    { key: 'building_profile', title: 'Profile', icon: <Brain className="w-4 h-4" /> },
  ];

  // Check if we can complete
  const requiredComplete = progress?.steps
    .filter(s => s.priority === 'required')
    .every(s => s.status === 'completed' || s.status === 'skipped');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold mb-2">Let's Set Up {assistantName}</h1>
        <p className="text-muted-foreground">
          Connect your accounts so I can help you better
        </p>
      </div>

      {/* Progress bar */}
      {progress && (
        <div className="relative h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 to-violet-600 transition-all duration-500"
            style={{ width: `${progress.percent_complete}%` }}
          />
        </div>
      )}

      {/* System info */}
      {systemInfo.platform && (
        <div className="text-xs text-muted-foreground text-center">
          Detected: {systemInfo.platform}
          {systemInfo.email_clients?.length ? ` | Email: ${systemInfo.email_clients.join(', ')}` : ''}
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-500">
          {error}
        </div>
      )}

      {/* Steps grouped by phase */}
      <div className="space-y-6">
        {phases.map(phase => {
          const phaseSteps = stepsByPhase[phase.key];
          if (!phaseSteps?.length) return null;

          return (
            <div key={phase.key}>
              <div className="flex items-center gap-2 mb-3">
                {phase.icon}
                <h2 className="font-semibold text-sm">{phase.title}</h2>
              </div>
              <div className="space-y-2">
                {phaseSteps.map(step => renderStepCard(step))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Complete button */}
      <div className="pt-4 border-t">
        <button
          onClick={completeSetup}
          disabled={!requiredComplete}
          className={`
            w-full py-3 px-4 rounded-xl font-medium transition
            ${requiredComplete
              ? 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:opacity-90'
              : 'bg-muted text-muted-foreground cursor-not-allowed'
            }
          `}
        >
          {requiredComplete ? 'Complete Setup' : 'Complete required steps first'}
        </button>
        {!requiredComplete && (
          <p className="text-xs text-muted-foreground text-center mt-2">
            You can skip optional steps, but required ones must be completed
          </p>
        )}
      </div>
    </div>
  );
}
