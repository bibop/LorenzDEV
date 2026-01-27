import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Sparkles, MessageSquare, FileText, Cpu } from "lucide-react";
import Link from "next/link";

export default function WelcomePage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-background to-muted p-4">
            <div className="w-full max-w-4xl space-y-8">
                {/* Hero Section */}
                <div className="text-center space-y-4">
                    <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
                        <Sparkles className="h-4 w-4" />
                        <span>LORENZ UI Beta</span>
                    </div>

                    <h1 className="text-6xl font-bold tracking-tight">
                        Welcome to{" "}
                        <span className="bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                            LORENZ
                        </span>
                    </h1>

                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Your professional AI-powered SaaS platform with advanced RAG, unified skills, and digital twin capabilities
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                        <CardHeader>
                            <MessageSquare className="h-8 w-8 text-primary mb-2" />
                            <CardTitle>AI Chat</CardTitle>
                            <CardDescription>
                                Conversational AI with context-aware responses and streaming
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card>
                        <CardHeader>
                            <FileText className="h-8 w-8 text-primary mb-2" />
                            <CardTitle>Smart Documents</CardTitle>
                            <CardDescription>
                                Upload and search documents with hybrid RAG technology
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card>
                        <CardHeader>
                            <Cpu className="h-8 w-8 text-primary mb-2" />
                            <CardTitle>Unified Skills</CardTitle>
                            <CardDescription>
                                Execute powerful tools and create emergent workflows
                            </CardDescription>
                        </CardHeader>
                    </Card>
                </div>

                {/* CTA */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link href="/register">
                        <Button size="lg" className="text-base w-full sm:w-auto">
                            Get Started
                        </Button>
                    </Link>
                    <Link href="/login">
                        <Button size="lg" variant="outline" className="text-base w-full sm:w-auto">
                            Sign In
                        </Button>
                    </Link>
                </div>

                {/* Status Badge */}
                <div className="text-center">
                    <p className="text-sm text-muted-foreground">
                        🚧 Under Active Development • Phase 1 MVP
                    </p>
                </div>
            </div>
        </div>
    );
}
