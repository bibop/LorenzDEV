'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { VoiceSelector } from './voice-selector';
import { voiceAPI, Voice, PersonaCreate } from '@/lib/voice-api';
import { Loader2, CheckCircle2, Sparkles } from 'lucide-react';

interface PersonaEditorProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
    editPersonaId?: string;
}

export function PersonaEditor({
    open,
    onOpenChange,
    onSuccess,
    editPersonaId,
}: PersonaEditorProps) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [rolePrompt, setRolePrompt] = useState('');
    const [voiceId, setVoiceId] = useState('');
    const [isPublic, setIsPublic] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [error, setError] = useState('');

    // Load persona if editing
    useEffect(() => {
        if (open && editPersonaId) {
            loadPersona(editPersonaId);
        } else if (open) {
            resetForm();
        }
    }, [open, editPersonaId]);

    const loadPersona = async (id: string) => {
        try {
            const persona = await voiceAPI.getPersona(id);
            setName(persona.name);
            setDescription(persona.description || '');
            setRolePrompt(persona.role_prompt);
            setVoiceId(persona.voice_id);
            setIsPublic(persona.is_public);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load persona');
        }
    };

    const resetForm = () => {
        setName('');
        setDescription('');
        setRolePrompt('');
        setVoiceId('');
        setIsPublic(false);
        setError('');
        setSaveSuccess(false);
    };

    const handleSave = async () => {
        if (!name || !rolePrompt || !voiceId) {
            setError('Please fill in all required fields');
            return;
        }

        setIsSaving(true);
        setError('');

        try {
            const personaData: PersonaCreate = {
                name,
                description: description || undefined,
                role_prompt: rolePrompt,
                voice_id: voiceId,
                is_public: isPublic,
            };

            if (editPersonaId) {
                await voiceAPI.updatePersona(editPersonaId, personaData);
            } else {
                await voiceAPI.createPersona(personaData);
            }

            setSaveSuccess(true);
            setTimeout(() => {
                onSuccess?.();
                handleClose();
            }, 1500);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Save failed');
        } finally {
            setIsSaving(false);
        }
    };

    const handleClose = () => {
        resetForm();
        onOpenChange(false);
    };

    // Preset role templates
    const roleTemplates = [
        {
            name: 'Customer Support Agent',
            prompt: 'You are a helpful and patient customer support agent. Your goal is to understand customer issues and provide clear, actionable solutions. Always be polite and empathetic.',
        },
        {
            name: 'Technical Expert',
            prompt: 'You are a knowledgeable technical expert. Provide accurate, detailed technical information while explaining complex concepts in an understandable way. Use examples when helpful.',
        },
        {
            name: 'Creative Consultant',
            prompt: 'You are an enthusiastic creative consultant. Help users brainstorm ideas, explore creative possibilities, and think outside the box. Be encouraging and inspiring.',
        },
        {
            name: 'Professional Assistant',
            prompt: 'You are a professional executive assistant. Help with scheduling, organization, and task management. Be concise, efficient, and proactive in offering solutions.',
        },
    ];

    const applyTemplate = (template: typeof roleTemplates[0]) => {
        if (!name) setName(template.name);
        setRolePrompt(template.prompt);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        {editPersonaId ? 'Edit Persona' : 'Create AI Persona'}
                    </DialogTitle>
                    <DialogDescription>
                        Combine a voice with a role to create a unique AI persona
                    </DialogDescription>
                </DialogHeader>

                {saveSuccess ? (
                    <div className="flex flex-col items-center justify-center py-8">
                        <CheckCircle2 className="h-16 w-16 text-green-500 mb-4" />
                        <p className="text-lg font-medium">
                            Persona {editPersonaId ? 'updated' : 'created'} successfully!
                        </p>
                    </div>
                ) : (
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                                {error}
                            </div>
                        )}

                        {/* Basic Info */}
                        <div className="space-y-2">
                            <Label htmlFor="persona-name">Persona Name *</Label>
                            <Input
                                id="persona-name"
                                placeholder="e.g., Sarah the Support Agent"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                disabled={isSaving}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="persona-desc">Description</Label>
                            <Input
                                id="persona-desc"
                                placeholder="Brief description of this persona"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                disabled={isSaving}
                            />
                        </div>

                        {/* Voice Selection */}
                        <div className="space-y-2">
                            <Label>Voice *</Label>
                            <VoiceSelector value={voiceId} onChange={setVoiceId} disabled={isSaving} />
                            <p className="text-xs text-muted-foreground">
                                Choose the voice this persona will use
                            </p>
                        </div>

                        {/* Role Prompt */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="role-prompt">Role & Behavior *</Label>
                                <div className="text-xs text-muted-foreground">
                                    Use templates:
                                </div>
                            </div>
                            <div className="flex gap-2 flex-wrap mb-2">
                                {roleTemplates.map((template) => (
                                    <Button
                                        key={template.name}
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => applyTemplate(template)}
                                        disabled={isSaving}
                                    >
                                        {template.name}
                                    </Button>
                                ))}
                            </div>
                            <Textarea
                                id="role-prompt"
                                placeholder="Describe the persona's role, personality, and how it should behave..."
                                value={rolePrompt}
                                onChange={(e) => setRolePrompt(e.target.value)}
                                disabled={isSaving}
                                rows={6}
                                className="resize-none"
                            />
                            <p className="text-xs text-muted-foreground">
                                This defines how the AI will act and respond in conversations
                            </p>
                        </div>

                        {/* Public Toggle */}
                        <div className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                id="persona-public"
                                checked={isPublic}
                                onChange={(e) => setIsPublic(e.target.checked)}
                                disabled={isSaving}
                                className="rounded border-gray-300"
                            />
                            <Label htmlFor="persona-public" className="text-sm font-normal cursor-pointer">
                                Make this persona public (visible to all team members)
                            </Label>
                        </div>
                    </div>
                )}

                {!saveSuccess && (
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={handleClose} disabled={isSaving}>
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            onClick={handleSave}
                            disabled={isSaving || !name || !rolePrompt || !voiceId}
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="mr-2 h-4 w-4" />
                                    {editPersonaId ? 'Update' : 'Create'} Persona
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                )}
            </DialogContent>
        </Dialog>
    );
}
