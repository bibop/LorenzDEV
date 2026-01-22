'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

interface ResponseProps extends React.HTMLAttributes<HTMLDivElement> {
  children: string;
  streaming?: boolean;
}

const Response = React.memo(
  React.forwardRef<HTMLDivElement, ResponseProps>(
    ({ className, children, streaming = false, ...props }, ref) => {
      return (
        <div
          ref={ref}
          className={cn(
            'streamdown text-foreground/90',
            streaming && 'streaming',
            className
          )}
          {...props}
        >
          <ReactMarkdown
            components={{
              // Headings
              h1: ({ children }) => (
                <h1 className="text-xl font-medium text-foreground mt-6 mb-3 first:mt-0">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-lg font-medium text-foreground mt-5 mb-2 first:mt-0">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base font-medium text-foreground mt-4 mb-2 first:mt-0">
                  {children}
                </h3>
              ),
              // Paragraph
              p: ({ children }) => (
                <p className="my-2 leading-relaxed first:mt-0 last:mb-0">
                  {children}
                </p>
              ),
              // Lists
              ul: ({ children }) => (
                <ul className="my-2 pl-5 list-disc space-y-1 first:mt-0 last:mb-0">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="my-2 pl-5 list-decimal space-y-1 first:mt-0 last:mb-0">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="leading-relaxed">{children}</li>
              ),
              // Code
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                if (isInline) {
                  return (
                    <code className="bg-muted/50 px-1.5 py-0.5 rounded text-sm font-mono text-primary">
                      {children}
                    </code>
                  );
                }
                return (
                  <code className={cn('font-mono text-sm', className)} {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({ children }) => (
                <pre className="bg-muted/50 p-4 rounded-xl my-3 overflow-x-auto border border-border text-sm first:mt-0 last:mb-0">
                  {children}
                </pre>
              ),
              // Blockquote
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 border-primary/30 pl-4 my-3 italic text-muted-foreground first:mt-0 last:mb-0">
                  {children}
                </blockquote>
              ),
              // Links
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  {children}
                </a>
              ),
              // Strong and emphasis
              strong: ({ children }) => (
                <strong className="font-medium text-foreground">{children}</strong>
              ),
              em: ({ children }) => (
                <em className="italic">{children}</em>
              ),
              // Horizontal rule
              hr: () => <hr className="my-4 border-border" />,
              // Table
              table: ({ children }) => (
                <div className="my-3 overflow-x-auto first:mt-0 last:mb-0">
                  <table className="w-full border-collapse text-sm">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-muted/50">{children}</thead>
              ),
              th: ({ children }) => (
                <th className="border border-border px-4 py-2 text-left font-medium">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-border px-4 py-2">{children}</td>
              ),
            }}
          >
            {children}
          </ReactMarkdown>
          {streaming && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-primary/50 animate-pulse rounded-sm" />
          )}
        </div>
      );
    }
  )
);

Response.displayName = 'Response';

export { Response };
