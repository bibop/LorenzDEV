'use client';

import { useState, useRef } from 'react';
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
import { voiceAPI } from '@/lib/voice-api';
import { Upload, Mic, Loader2, CheckCircle2 } from 'lucide-react';

interface VoiceUploaderProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
}

export function VoiceUploader({ open, onOpenChange, onSuccess }: VoiceUploaderProps) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [isPublic, setIsPublic] = useState(false);
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [error, setError] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('audio/')) {
            setError('Please select an audio file');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            setError('File size must be less than 10MB');
            return;
        }

        setAudioFile(file);
        setError('');

        // Auto-fill name from filename if empty
        if (!name) {
            setName(file.name.replace(/\.[^/.]+$/, ''));
        }
    };

    const handleUpload = async () => {
        if (!audioFile || !name) {
            setError('Please provide a name and select an audio file');
            return;
        }

        setIsUploading(true);
        setError('');

        try {
            await voiceAPI.uploadVoice({
                name,
                description: description || undefined,
                is_public: isPublic,
                audio_file: audioFile,
            });

            setUploadSuccess(true);
            setTimeout(() => {
                onSuccess?.();
                handleClose();
            }, 1500);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    const handleClose = () => {
        setName('');
        setDescription('');
        setIsPublic(false);
        setAudioFile(null);
        setError('');
        setUploadSuccess(false);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Upload Voice Sample</DialogTitle>
                    <DialogDescription>
                        Upload a clear audio sample (3-10 seconds) to create a custom voice
                    </DialogDescription>
                </DialogHeader>

                {uploadSuccess ? (
                    <div className="flex flex-col items-center justify-center py-8">
                        <CheckCircle2 className="h-16 w-16 text-green-500 mb-4" />
                        <p className="text-lg font-medium">Voice uploaded successfully!</p>
                    </div>
                ) : (
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="name">Voice Name *</Label>
                            <Input
                                id="name"
                                placeholder="e.g., Professional Assistant"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                disabled={isUploading}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                placeholder="Describe this voice..."
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                disabled={isUploading}
                                rows={3}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Audio Sample *</Label>
                            <div className="flex gap-2">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isUploading}
                                    className="flex-1"
                                >
                                    <Upload className="mr-2 h-4 w-4" />
                                    {audioFile ? audioFile.name : 'Choose File'}
                                </Button>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="audio/*"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />
                            </div>
                            {audioFile && (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Mic className="h-4 w-4" />
                                    <span>{(audioFile.size / 1024 / 1024).toFixed(2)} MB</span>
                                </div>
                            )}
                            <p className="text-xs text-muted-foreground">
                                Supported: WAV, MP3, M4A (max 10MB)
                            </p>
                        </div>

                        <div className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                id="is_public"
                                checked={isPublic}
                                onChange={(e) => setIsPublic(e.target.checked)}
                                disabled={isUploading}
                                className="rounded border-gray-300"
                            />
                            <Label htmlFor="is_public" className="text-sm font-normal cursor-pointer">
                                Make this voice public (visible to all team members)
                            </Label>
                        </div>
                    </div>
                )}

                {!uploadSuccess && (
                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleClose}
                            disabled={isUploading}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            onClick={handleUpload}
                            disabled={isUploading || !name || !audioFile}
                        >
                            {isUploading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Uploading...
                                </>
                            ) : (
                                <>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Upload Voice
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                )}
            </DialogContent>
        </Dialog>
    );
}
