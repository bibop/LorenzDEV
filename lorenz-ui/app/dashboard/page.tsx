'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, FileText, Cpu, Settings, LogOut } from 'lucide-react';

export default function DashboardPage() {
    const router = useRouter();

    useEffect(() => {
        // Check authentication
        if (!api.isAuthenticated()) {
            router.push('/login');
            return;
        }
    }, [router]);

    const handleLogout = () => {
        api.logout();
        router.push('/login');
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
            {/* Header */}
            <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container flex items-center justify-between py-4">
                    <h1 className="text-2xl font-bold">LORENZ Dashboard</h1>
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard/settings')}>
                            <Settings className="h-5 w-5" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={handleLogout}>
                            <LogOut className="h-5 w-5" />
                        </Button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="container py-8">
                <div className="space-y-8">
                    {/* Welcome Section */}
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight mb-2">Welcome back!</h2>
                        <p className="text-muted-foreground">Choose a feature to get started</p>
                    </div>

                    {/* Feature Cards */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card
                            className="cursor-pointer hover:shadow-lg transition-shadow"
                            onClick={() => router.push('/dashboard/chat')}
                        >
                            <CardHeader>
                                <MessageSquare className="h-8 w-8 text-primary mb-2" />
                                <CardTitle>AI Chat</CardTitle>
                                <CardDescription>
                                    Start a conversation with your AI assistant
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Button className="w-full">Open Chat</Button>
                            </CardContent>
                        </Card>

                        <Card className="cursor-pointer hover:shadow-lg transition-shadow opacity-50">
                            <CardHeader>
                                <FileText className="h-8 w-8 text-primary mb-2" />
                                <CardTitle>Documents</CardTitle>
                                <CardDescription>
                                    Upload and search through your documents
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Button className="w-full" disabled>Coming Soon</Button>
                            </CardContent>
                        </Card>

                        <Card className="cursor-pointer hover:shadow-lg transition-shadow opacity-50">
                            <CardHeader>
                                <Cpu className="h-8 w-8 text-primary mb-2" />
                                <CardTitle>Skills</CardTitle>
                                <CardDescription>
                                    Execute tools and manage workflows
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Button className="w-full" disabled>Coming Soon</Button>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Stats Section */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Total Conversations</CardDescription>
                                <CardTitle className="text-4xl">0</CardTitle>
                            </CardHeader>
                        </Card>

                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Documents Uploaded</CardDescription>
                                <CardTitle className="text-4xl">0</CardTitle>
                            </CardHeader>
                        </Card>

                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Skills Available</CardDescription>
                                <CardTitle className="text-4xl">12</CardTitle>
                            </CardHeader>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}
