'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import * as AvatarPrimitive from '@radix-ui/react-avatar';

// Message container
interface MessageProps extends React.HTMLAttributes<HTMLDivElement> {
  from: 'user' | 'assistant';
}

const Message = React.forwardRef<HTMLDivElement, MessageProps>(
  ({ className, from, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-from={from}
        className={cn(
          'group flex gap-3 animate-fade-in',
          from === 'user' ? 'flex-row-reverse' : 'flex-row',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Message.displayName = 'Message';

// Message content
interface MessageContentProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'contained' | 'flat';
}

const MessageContent = React.forwardRef<HTMLDivElement, MessageContentProps>(
  ({ className, variant = 'contained', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'max-w-[85%] md:max-w-[75%]',
          variant === 'contained' && [
            'px-4 py-3 rounded-2xl',
            'group-data-[from=user]:bg-primary/15 group-data-[from=user]:rounded-br-sm',
            'group-data-[from=assistant]:bg-muted group-data-[from=assistant]:rounded-bl-sm',
          ],
          variant === 'flat' && 'text-foreground/90',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
MessageContent.displayName = 'MessageContent';

// Message avatar
interface MessageAvatarProps extends React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Root> {
  src?: string;
  name?: string;
}

const MessageAvatar = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Root>,
  MessageAvatarProps
>(({ className, src, name, ...props }, ref) => {
  return (
    <AvatarPrimitive.Root
      ref={ref}
      className={cn(
        'relative flex h-9 w-9 shrink-0 overflow-hidden rounded-full',
        'ring-1 ring-border/50',
        className
      )}
      {...props}
    >
      {src && (
        <AvatarPrimitive.Image
          src={src}
          alt={name || 'Avatar'}
          className="aspect-square h-full w-full object-cover"
        />
      )}
      <AvatarPrimitive.Fallback
        className={cn(
          'flex h-full w-full items-center justify-center rounded-full',
          'bg-gradient-to-br from-primary/20 to-secondary/20',
          'text-sm font-medium text-foreground/70'
        )}
      >
        {name?.slice(0, 2).toUpperCase() || '?'}
      </AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  );
});
MessageAvatar.displayName = 'MessageAvatar';

// Message timestamp
interface MessageTimeProps extends React.HTMLAttributes<HTMLSpanElement> {
  time: Date | string;
}

const MessageTime = React.forwardRef<HTMLSpanElement, MessageTimeProps>(
  ({ className, time, ...props }, ref) => {
    const formattedTime = React.useMemo(() => {
      const date = typeof time === 'string' ? new Date(time) : time;
      return date.toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit',
      });
    }, [time]);

    return (
      <span
        ref={ref}
        className={cn('text-xs text-muted-foreground/60', className)}
        {...props}
      >
        {formattedTime}
      </span>
    );
  }
);
MessageTime.displayName = 'MessageTime';

// Message metadata (for showing badges like RAG, Twin, etc.)
interface MessageMetadataProps extends React.HTMLAttributes<HTMLDivElement> {}

const MessageMetadata = React.forwardRef<HTMLDivElement, MessageMetadataProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex flex-wrap items-center gap-1.5 mt-2', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
MessageMetadata.displayName = 'MessageMetadata';

// Message badge
interface MessageBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'lavender' | 'blue' | 'mint' | 'peach' | 'rose';
  icon?: React.ReactNode;
}

const MessageBadge = React.forwardRef<HTMLSpanElement, MessageBadgeProps>(
  ({ className, variant = 'lavender', icon, children, ...props }, ref) => {
    const variantClasses = {
      lavender: 'chip-lavender',
      blue: 'chip-blue',
      mint: 'chip-mint',
      peach: 'chip-peach',
      rose: 'chip-rose',
    };

    return (
      <span
        ref={ref}
        className={cn('chip', variantClasses[variant], className)}
        {...props}
      >
        {icon && <span className="w-3 h-3">{icon}</span>}
        {children}
      </span>
    );
  }
);
MessageBadge.displayName = 'MessageBadge';

export {
  Message,
  MessageContent,
  MessageAvatar,
  MessageTime,
  MessageMetadata,
  MessageBadge,
};
