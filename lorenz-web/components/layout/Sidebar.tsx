"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    MessageSquare,
    Settings,
    Plus,
    LogOut,
    PanelLeftClose,
    PanelLeftOpen,
    User,
    History
} from "lucide-react";

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const [collapsed, setCollapsed] = useState(false);
    const pathname = usePathname();

    const toggleSidebar = () => setCollapsed(!collapsed);

    return (
        <div
            className={cn(
                "relative flex flex-col h-screen border-r bg-card/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
                collapsed ? "w-[60px]" : "w-[280px]",
                className
            )}
        >
            {/* Header / New Chat */}
            <div className="flex items-center justify-between p-4 h-16 border-b border-border/50">
                {!collapsed && (
                    <Button
                        variant="outline"
                        className="w-full justify-start gap-2 bg-background/50 border-dashed border-border hover:bg-background/80 hover:border-primary/50 transition-all font-medium text-sm text-muted-foreground hover:text-foreground"
                    >
                        <Plus className="h-4 w-4" />
                        New Chat
                    </Button>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleSidebar}
                    className={cn("text-muted-foreground hover:text-foreground", collapsed ? "mx-auto" : "ml-2")}
                >
                    {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
                </Button>
            </div>

            {/* Main Content (History) */}
            <ScrollArea className="flex-1 px-2 py-4">
                {!collapsed ? (
                    <div className="space-y-6">
                        <div className="space-y-1">
                            <h3 className="px-2 text-xs font-semibold text-muted-foreground/60 uppercase tracking-wider mb-2">Today</h3>
                            <SidebarItem active={true} icon={MessageSquare} label="Project Lorenz Architecture" />
                            <SidebarItem icon={MessageSquare} label="Refactoring UI components" />
                            <SidebarItem icon={MessageSquare} label="Meeting notes synthesis" />
                        </div>

                        <div className="space-y-1">
                            <h3 className="px-2 text-xs font-semibold text-muted-foreground/60 uppercase tracking-wider mb-2">Yesterday</h3>
                            <SidebarItem icon={History} label="Post-deployment analysis" />
                            <SidebarItem icon={History} label="Bug fix #402 discussion" />
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-4">
                        <SidebarIcon icon={MessageSquare} active />
                        <SidebarIcon icon={History} />
                        <SidebarIcon icon={History} />
                    </div>
                )}
            </ScrollArea>

            {/* Footer / User Profile */}
            <div className="p-4 border-t border-border/50">
                {!collapsed ? (
                    <div className="flex items-center gap-3 w-full">
                        <Button variant="ghost" className="w-full justify-start gap-3 px-2 hover:bg-muted/50">
                            <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-primary/20 to-secondary/20 flex items-center justify-center border border-border/50">
                                <User className="h-4 w-4 text-foreground" />
                            </div>
                            <div className="flex flex-col items-start text-xs">
                                <span className="font-medium text-foreground">Bibop</span>
                                <span className="text-muted-foreground">Pro Plan</span>
                            </div>
                            <Settings className="ml-auto h-4 w-4 text-muted-foreground" />
                        </Button>
                    </div>
                ) : (
                    <div className="flex justify-center">
                        <Button variant="ghost" size="icon" className="rounded-full">
                            <User className="h-4 w-4" />
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}

function SidebarItem({ icon: Icon, label, active }: { icon: any; label: string; active?: boolean }) {
    return (
        <Button
            variant="ghost"
            className={cn(
                "w-full justify-start gap-3 h-9 px-3 text-sm font-normal transition-all",
                active
                    ? "bg-primary/10 text-primary hover:bg-primary/15"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
            )}
        >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="truncate">{label}</span>
        </Button>
    );
}

function SidebarIcon({ icon: Icon, active }: { icon: any; active?: boolean }) {
    return (
        <Button
            variant="ghost"
            size="icon"
            className={cn(
                "h-9 w-9 rounded-lg transition-all",
                active
                    ? "bg-primary/10 text-primary hover:bg-primary/15"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
            )}
        >
            <Icon className="h-4 w-4" />
        </Button>
    );
}
