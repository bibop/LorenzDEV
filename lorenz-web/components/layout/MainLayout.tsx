"use client";

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface MainLayoutProps {
    children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="flex h-screen w-full bg-background overflow-hidden relative">
            {/* Background decoration - subtle gradient orb */}
            <div className="fixed top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px] pointer-events-none z-0" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-secondary/5 blur-[140px] pointer-events-none z-0" />

            <Sidebar className="z-10" />

            <main className="flex-1 flex flex-col relative z-0 overflow-hidden">
                {children}
            </main>
        </div>
    );
}
