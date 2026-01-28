'use client';

import React from 'react';

interface ErrorBoundaryProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        // Update state so the next render will show the fallback UI
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // Log error to console
        console.error('ErrorBoundary caught an error:', error, errorInfo);

        // Ignore hydration errors in development
        if (error.message?.includes('Hydration') || error.message?.includes('hydration')) {
            console.warn('Hydration error detected, attempting recovery...');
            // Reset error state after a brief delay to retry rendering
            setTimeout(() => {
                this.setState({ hasError: false });
            }, 100);
        }
    }

    render() {
        if (this.state.hasError && this.props.fallback) {
            return this.props.fallback;
        }

        return this.props.children;
    }
}
