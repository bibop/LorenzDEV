import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Sparkles, MessageSquare, FileText, Cpu } from "lucide-react";
import Link from "next/link";

export default function WelcomePage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center aurora-bg p-4 overflow-hidden relative">
            {/* Ambient background glows */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] animae-pulse" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 rounded-full blur-[120px] animate-pulse" />

            <div className="w-full max-w-4xl space-y-12 z-10">
                {/* Hero Section */}
                <div className="text-center space-y-6 animate-float">
                    <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary backdrop-blur-md">
                        <Sparkles className="h-4 w-4" />
                        <span>LORENZ AI Evolution</span>
                    </div>

                    <h1 className="text-7xl font-extrabold tracking-tighter leading-tight">
                        Experience{" "}
                        <span className="bg-gradient-to-r from-primary via-violet-400 to-fuchsia-500 bg-clip-text text-transparent text-glow">
                            Intelligence
                        </span>
                    </h1>

                    <p className="text-xl text-muted-foreground/80 max-w-2xl mx-auto leading-relaxed">
                        LORENZ is your professional AI-powered ecosystem.
                        Advanced RAG, unified skills, and digital twin technology,
                        crafted for the next era of productivity.
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid gap-6 md:grid-cols-3">
                    <Card className="bg-background/40 backdrop-blur-xl border-primary/10 hover:border-primary/30 transition-all duration-500 group">
                        <CardHeader>
                            <div className="p-3 w-fit rounded-2xl bg-primary/10 group-hover:bg-primary/20 transition-colors mb-4">
                                <MessageSquare className="h-8 w-8 text-primary" />
                            </div>
                            <CardTitle className="text-xl">AI Core</CardTitle>
                            <CardDescription className="text-base">
                                Neural-native chat with multi-model orchestrator and real-time streaming.
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="bg-background/40 backdrop-blur-xl border-primary/10 hover:border-primary/30 transition-all duration-500 group">
                        <CardHeader>
                            <div className="p-3 w-fit rounded-2xl bg-primary/10 group-hover:bg-primary/20 transition-colors mb-4">
                                <FileText className="h-8 w-8 text-primary" />
                            </div>
                            <CardTitle className="text-xl">Mneme Engine</CardTitle>
                            <CardDescription className="text-base">
                                Semantic memory system with hybrid search and late-interaction reranking.
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="bg-background/40 backdrop-blur-xl border-primary/10 hover:border-primary/30 transition-all duration-500 group">
                        <CardHeader>
                            <div className="p-3 w-fit rounded-2xl bg-primary/10 group-hover:bg-primary/20 transition-colors mb-4">
                                <Cpu className="h-8 w-8 text-primary" />
                            </div>
                            <CardTitle className="text-xl">Twin Sync</CardTitle>
                            <CardDescription className="text-base">
                                Your digital replica with cloned voice, emergent skills, and personalized logic.
                            </CardDescription>
                        </CardHeader>
                    </Card>
                </div>

                {/* CTA */}
                <div className="flex flex-col sm:row gap-6 justify-center">
                    <Link href="/register">
                        <Button size="lg" className="h-14 px-10 text-lg font-bold rounded-2xl bg-primary hover:bg-primary/90 shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all duration-300">
                            Launch Interface
                        </Button>
                    </Link>
                    <Link href="/login">
                        <Button size="lg" variant="outline" className="h-14 px-10 text-lg font-semibold rounded-2xl border-primary/20 hover:bg-primary/5 backdrop-blur-sm transition-all duration-300">
                            Already Member
                        </Button>
                    </Link>
                </div>

                {/* Status Badge */}
                <div className="text-center pt-8">
                    <div className="inline-block px-4 py-1.5 rounded-full bg-muted/50 text-xs font-mono text-muted-foreground border border-border/50">
                        SYSTEM STATUS: PLATFORM CORE STABLE • ALPHA RELEASE 1.2
                    </div>
                </div>
            </div>
        </div>
    );
}
