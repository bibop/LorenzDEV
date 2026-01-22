'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Mic, MicOff, Loader2, Check, X } from 'lucide-react';

type VoiceButtonState = 'idle' | 'recording' | 'processing' | 'success' | 'error';

interface VoiceButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  state?: VoiceButtonState;
  onPress?: () => void;
  label?: React.ReactNode;
  trailing?: React.ReactNode;
  icon?: React.ReactNode;
  variant?: 'default' | 'outline' | 'ghost' | 'pastel';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  feedbackDuration?: number;
}

const VoiceButton = React.forwardRef<HTMLButtonElement, VoiceButtonProps>(
  (
    {
      className,
      state = 'idle',
      onPress,
      label,
      trailing,
      icon,
      variant = 'outline',
      size = 'default',
      feedbackDuration = 1500,
      disabled,
      ...props
    },
    ref
  ) => {
    const [internalState, setInternalState] = React.useState<VoiceButtonState>(state);

    React.useEffect(() => {
      setInternalState(state);
    }, [state]);

    React.useEffect(() => {
      if (internalState === 'success' || internalState === 'error') {
        const timer = setTimeout(() => {
          setInternalState('idle');
        }, feedbackDuration);
        return () => clearTimeout(timer);
      }
    }, [internalState, feedbackDuration]);

    const getIcon = () => {
      switch (internalState) {
        case 'recording':
          return <MicOff className="w-5 h-5 text-destructive-foreground" />;
        case 'processing':
          return <Loader2 className="w-5 h-5 animate-spin" />;
        case 'success':
          return <Check className="w-5 h-5 text-accent-foreground" />;
        case 'error':
          return <X className="w-5 h-5 text-destructive-foreground" />;
        default:
          return icon || <Mic className="w-5 h-5" />;
      }
    };

    const variantClasses = {
      default: 'bg-primary text-primary-foreground hover:bg-primary/90',
      outline: 'border border-border bg-background hover:bg-muted',
      ghost: 'hover:bg-muted',
      pastel: 'bg-primary/15 text-primary hover:bg-primary/25',
    };

    const sizeClasses = {
      default: 'h-10 px-4 py-2',
      sm: 'h-9 px-3',
      lg: 'h-11 px-8',
      icon: 'h-10 w-10',
    };

    const stateClasses = {
      idle: '',
      recording: 'bg-destructive/15 text-destructive border-destructive/30 animate-pulse',
      processing: 'opacity-70 cursor-wait',
      success: 'bg-accent/15 text-accent-foreground border-accent/30',
      error: 'bg-destructive/15 text-destructive-foreground border-destructive/30',
    };

    return (
      <button
        ref={ref}
        onClick={onPress}
        disabled={disabled || internalState === 'processing'}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-xl',
          'font-medium transition-smooth',
          'focus:outline-none focus:ring-2 focus:ring-primary/30 focus:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          variantClasses[variant],
          sizeClasses[size],
          stateClasses[internalState],
          className
        )}
        {...props}
      >
        {label && <span>{label}</span>}
        {getIcon()}
        {trailing && <span className="text-muted-foreground text-sm">{trailing}</span>}
      </button>
    );
  }
);
VoiceButton.displayName = 'VoiceButton';

export { VoiceButton };
export type { VoiceButtonState, VoiceButtonProps };
