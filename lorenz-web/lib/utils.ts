import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: string | Date): string {
  const d = new Date(date);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Adesso';
  if (diffMins < 60) return `${diffMins}m fa`;
  if (diffHours < 24) return `${diffHours}h fa`;
  if (diffDays < 7) return `${diffDays}g fa`;
  return formatDate(date);
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    pattern: 'bg-blue-500',
    workflow: 'bg-purple-500',
    fact: 'bg-green-500',
    preference: 'bg-yellow-500',
    skill_memory: 'bg-pink-500',
  };
  return colors[category] || 'bg-gray-500';
}

export function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    pattern: 'Pattern',
    workflow: 'Workflow',
    fact: 'Fatto',
    preference: 'Preferenza',
    skill_memory: 'Memoria Skill',
  };
  return labels[category] || category;
}
