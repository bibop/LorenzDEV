'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sparkles, Loader2, ArrowRight, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        // Mock API call for now since backend might not have this endpoint yet
        try {
            await new Promise(resolve => setTimeout(resolve, 1500));
            toast.success('Recovery signal broadcasted. Check your communication channels.');
            setEmail('');
        } catch (err) {
            toast.error('Signal failed. Network unreachable.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="relative min-h-screen w-full overflow-hidden aurora-bg flex items-center justify-center p-4">
            {/* Background Orbs */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/20 blur-[100px] animate-float" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-blue-500/20 blur-[100px] animate-float" style={{ animationDelay: '-3s' }} />

            <div className="relative w-full max-w-lg">
                <div className="bg-black/40 backdrop-blur-xl border border-white/10 shadow-2xl rounded-3xl p-8 md:p-12 space-y-8">
                    {/* Header */}
                    <div className="text-center space-y-2">
                        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm font-medium text-white/90 shadow-lg backdrop-blur-md">
                            <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                            <span>LORENZ OS</span>
                            <span className="text-yellow-500 text-xs ml-2">● RECOVERY MODE</span>
                        </div>
                        <h1 className="text-4xl font-bold tracking-tight text-white text-glow mt-4">
                            Restore Access
                        </h1>
                        <p className="text-white/60">
                            Initiate identity recovery protocol.
                        </p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-white/80">Identity / Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="name@domain.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                                className="bg-white/5 border-white/10 text-white placeholder:text-white/20 h-12 focus:bg-white/10 transition-all rounded-xl"
                            />
                        </div>

                        <Button
                            type="submit"
                            className="w-full h-12 bg-primary hover:bg-primary/90 text-white font-bold rounded-xl shadow-[0_0_30px_-5px_rgba(139,92,246,0.5)] transition-all hover:shadow-[0_0_50px_-5px_rgba(139,92,246,0.7)] hover:scale-[1.02]"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Broadcasting...
                                </>
                            ) : (
                                <span className="flex items-center gap-2">
                                    Send Recovery Signal <ArrowRight className="h-4 w-4" />
                                </span>
                            )}
                        </Button>
                    </form>

                    <div className="text-center">
                        <Link
                            href="/login"
                            className="text-sm text-white/50 hover:text-white transition-colors hover:underline decoration-primary/50 underline-offset-4 flex items-center justify-center gap-2"
                        >
                            <ArrowLeft className="h-4 w-4" /> Abort Recovery
                        </Link>
                    </div>
                </div>

                {/* Footer aesthetic text */}
                <div className="mt-8 text-center text-xs text-white/20 font-mono">
                    LORENZ SYSTEM V3.0 // SECURE CONNECTION ESTABLISHED
                </div>
            </div>
        </div>
    );
}
