'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useStickToBottom, StickToBottom } from 'use-stick-to-bottom';
import { ChevronDown, MessageCircle } from 'lucide-react';

// Conversation container with auto-scroll
interface ConversationProps {
  className?: string;
  children?: React.ReactNode;
}

const Conversation = ({ className, children }: ConversationProps) => {
  return (
    <StickToBottom
      className={cn('relative flex flex-col h-full overflow-hidden', className)}
      resize="smooth"
      initial="smooth"
    >
      {children}
    </StickToBottom>
  );
};
Conversation.displayName = 'Conversation';

// Conversation content wrapper
interface ConversationContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const ConversationContent = React.forwardRef<HTMLDivElement, ConversationContentProps>(
  ({ className, children, ...props }, ref) => {
    const { scrollRef, contentRef } = useStickToBottom();

    return (
      <div
        ref={(node) => {
          scrollRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref) ref.current = node;
        }}
        className={cn(
          'flex-1 overflow-y-auto overflow-x-hidden',
          'scroll-smooth',
          className
        )}
        {...props}
      >
        <div ref={contentRef} className="flex flex-col gap-4 p-4">
          {children}
        </div>
      </div>
    );
  }
);
ConversationContent.displayName = 'ConversationContent';

// Empty state
interface ConversationEmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}

const ConversationEmptyState = React.forwardRef<HTMLDivElement, ConversationEmptyStateProps>(
  ({ className, title = 'Nessun messaggio', description, icon, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex flex-col items-center justify-center h-full text-center p-8',
          className
        )}
        {...props}
      >
        {children || (
          <>
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              {icon || <MessageCircle className="w-8 h-8 text-muted-foreground/50" />}
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">{title}</h3>
            {description && (
              <p className="text-muted-foreground text-sm max-w-md">{description}</p>
            )}
          </>
        )}
      </div>
    );
  }
);
ConversationEmptyState.displayName = 'ConversationEmptyState';

// Scroll to bottom button
interface ConversationScrollButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

const ConversationScrollButton = React.forwardRef<HTMLButtonElement, ConversationScrollButtonProps>(
  ({ className, ...props }, ref) => {
    const { isAtBottom, scrollToBottom } = useStickToBottom();

    if (isAtBottom) return null;

    return (
      <button
        ref={ref}
        onClick={() => scrollToBottom()}
        className={cn(
          'absolute bottom-4 left-1/2 -translate-x-1/2',
          'flex items-center gap-1.5 px-3 py-1.5',
          'bg-card shadow-soft-lg border border-border rounded-full',
          'text-sm text-muted-foreground hover:text-foreground',
          'transition-smooth',
          className
        )}
        {...props}
      >
        <ChevronDown className="w-4 h-4" />
        <span>Nuovi messaggi</span>
      </button>
    );
  }
);
ConversationScrollButton.displayName = 'ConversationScrollButton';

// Typing indicator
interface ConversationTypingProps extends React.HTMLAttributes<HTMLDivElement> {
  name?: string;
}

const ConversationTyping = React.forwardRef<HTMLDivElement, ConversationTypingProps>(
  ({ className, name = 'Lorenz', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-center gap-2 text-muted-foreground text-sm', className)}
        {...props}
      >
        <div className="flex gap-1">
          <span className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <span>{name} sta scrivendo...</span>
      </div>
    );
  }
);
ConversationTyping.displayName = 'ConversationTyping';

export {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
  ConversationTyping,
};
