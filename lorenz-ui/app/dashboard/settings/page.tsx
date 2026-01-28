'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VoiceSettings } from '@/components/voice/voice-settings';
import {
    User,
    Lock,
    Bell,
    Shield,
    Sparkles,
    ArrowLeft,
    Save,
    Loader2,
    Mic
} from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');

    // Voice settings state
    const [selectedProvider, setSelectedProvider] = useState<'personaplex' | 'elevenlabs'>('elevenlabs');
    const [selectedVoice, setSelectedVoice] = useState('');

    useEffect(() => {
        if (!api.isAuthenticated()) {
            router.push('/login');
            return;
        }

        // Fetch user data
        const fetchUser = async () => {
            try {
                const user = await api.getCurrentUser();
                setFullName(user.name || '');
                setEmail(user.email || '');
            } catch (err) {
                console.error('Failed to fetch user:', err);
            }
        };
        fetchUser();
    }, [router]);

    const handleSaveProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            // Mock API update
            await new Promise(resolve => setTimeout(resolve, 1000));
            toast.success('Identity profile updated successfully.');
        } catch (err) {
            toast.error('Failed to update profile.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="relative min-h-screen w-full overflow-hidden aurora-bg p-4 md:p-8">
            {/* Background Orbs */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/10 blur-[100px] animate-float" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-blue-500/10 blur-[100px] animate-float" style={{ animationDelay: '-3s' }} />

            <div className="relative max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-primary-foreground/60 mb-2 underline-offset-4 hover:text-white cursor-pointer transition-colors" onClick={() => router.push('/dashboard')}>
                            <ArrowLeft className="h-4 w-4" />
                            <span className="text-sm font-medium">Back to System</span>
                        </div>
                        <h1 className="text-4xl font-bold tracking-tight text-white text-glow">
                            Control Center
                        </h1>
                        <p className="text-white/60 font-mono text-sm">
                            CONFIGURE PERIPHERALS // SYSTEM SETTINGS // V4.2
                        </p>
                    </div>
                    <div className="hidden md:flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm font-medium text-white/90 shadow-lg backdrop-blur-md">
                        <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                        <span>LORENZ OS</span>
                    </div>
                </div>

                <div className="bg-black/40 backdrop-blur-xl border border-white/10 shadow-2xl rounded-3xl p-1 md:p-2">
                    <Tabs defaultValue="profile" className="w-full">
                        <div className="p-4 border-b border-white/10">
                            <TabsList className="bg-white/5 border border-white/10 p-1 h-12">
                                <TabsTrigger value="profile" className="data-[state=active]:bg-white/10 data-[state=active]:text-white">
                                    <User className="h-4 w-4 mr-2" />
                                    Identity
                                </TabsTrigger>
                                <TabsTrigger value="voice" className="data-[state=active]:bg-white/10 data-[state=active]:text-white">
                                    <Mic className="h-4 w-4 mr-2" />
                                    Voice Interface
                                </TabsTrigger>
                                <TabsTrigger value="security" className="data-[state=active]:bg-white/10 data-[state=active]:text-white">
                                    <Lock className="h-4 w-4 mr-2" />
                                    Security
                                </TabsTrigger>
                                <TabsTrigger value="system" className="data-[state=active]:bg-white/10 data-[state=active]:text-white">
                                    <Shield className="h-4 w-4 mr-2" />
                                    Kernel
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        <div className="p-6 md:p-8">
                            {/* Profile Settings */}
                            <TabsContent value="profile" className="mt-0 space-y-8 animate-in fade-in slide-in-from-bottom-2">
                                <form onSubmit={handleSaveProfile} className="max-w-2xl space-y-6">
                                    <div className="space-y-4">
                                        <div className="grid gap-2">
                                            <Label htmlFor="name" className="text-white/80">Full Alias</Label>
                                            <Input
                                                id="name"
                                                value={fullName}
                                                onChange={(e) => setFullName(e.target.value)}
                                                className="bg-white/5 border-white/10 text-white h-12 rounded-xl focus:bg-white/10"
                                            />
                                        </div>
                                        <div className="grid gap-2">
                                            <Label htmlFor="email" className="text-white/80">Identity / Email</Label>
                                            <Input
                                                id="email"
                                                type="email"
                                                value={email}
                                                disabled
                                                className="bg-white/5 border-white/10 text-white/50 h-12 rounded-xl"
                                            />
                                            <p className="text-xs text-white/40 italic">Identity cannot be modified after initialization.</p>
                                        </div>
                                    </div>

                                    <Button
                                        type="submit"
                                        className="bg-primary hover:bg-primary/90 text-white h-12 px-8 rounded-xl"
                                        disabled={isLoading}
                                    >
                                        {isLoading ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Processing...
                                            </>
                                        ) : (
                                            <>
                                                <Save className="mr-2 h-4 w-4" />
                                                Persist Changes
                                            </>
                                        )}
                                    </Button>
                                </form>
                            </TabsContent>

                            {/* Voice Settings */}
                            <TabsContent value="voice" className="mt-0 animate-in fade-in slide-in-from-bottom-2">
                                <div className="max-w-4xl">
                                    <VoiceSettings
                                        selectedProvider={selectedProvider}
                                        selectedVoice={selectedVoice}
                                        onProviderChange={(p) => setSelectedProvider(p as any)}
                                        onVoiceChange={setSelectedVoice}
                                    />
                                </div>
                            </TabsContent>

                            {/* Security Settings */}
                            <TabsContent value="security" className="mt-0 space-y-8 animate-in fade-in slide-in-from-bottom-2">
                                <div className="max-w-2xl space-y-6">
                                    <div className="grid gap-4">
                                        <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <div className="text-white font-medium">Passkey Rotation</div>
                                                <div className="text-white/50 text-sm">Last modified 14 cycles ago.</div>
                                            </div>
                                            <Button variant="outline" className="border-white/10 text-white hover:bg-white/5">Change Passkey</Button>
                                        </div>

                                        <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <div className="text-white font-medium">Neural Auth (2FA)</div>
                                                <div className="text-white/50 text-sm">Add an extra layer of protection.</div>
                                            </div>
                                            <Button variant="outline" className="border-white/10 text-white hover:bg-white/5">Configure</Button>
                                        </div>
                                    </div>
                                </div>
                            </TabsContent>

                            {/* System Settings */}
                            <TabsContent value="system" className="mt-0 animate-in fade-in slide-in-from-bottom-2">
                                <div className="p-8 rounded-2xl bg-primary/5 border border-primary/20 text-center space-y-4">
                                    <Shield className="h-12 w-12 text-primary mx-auto opacity-50" />
                                    <h3 className="text-xl font-bold text-white">Kernel Access Required</h3>
                                    <p className="text-white/60 max-w-sm mx-auto">
                                        Advanced system tuning requires higher privilege levels.
                                        Consult with the LORENZ architect for access.
                                    </p>
                                    <Button variant="ghost" className="text-primary hover:text-primary/80">Request Uplink</Button>
                                </div>
                            </TabsContent>
                        </div>
                    </Tabs>
                </div>

                <div className="text-center text-xs text-white/20 font-mono">
                    LORENZ SYSTEM V3.0 // BUILD 0924 // SECURE CONNECTION
                </div>
            </div>
        </div>
    );
}
