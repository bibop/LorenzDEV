/**
 * LORENZ SaaS - TypeScript Types
 */

// Authentication
export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  telegram_chat_id?: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Chat
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: {
    model?: string;
    skill_used?: string;
    tokens?: number;
    cost?: number;
    // Twin integration flags
    twin_processed?: boolean;
    rag_context_used?: boolean;
    mneme_context_used?: boolean;
    // Context details
    knowledge_sources?: number;
    semantic_sources?: number;
    calendar_events?: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

// Knowledge Base (MNEME)
export interface KnowledgeEntry {
  id: string;
  category: 'pattern' | 'workflow' | 'fact' | 'preference' | 'skill_memory';
  title: string;
  content: string;
  context: Record<string, any>;
  access_count: number;
  confidence: number;
  source: string;
  tags: string[];
  related_skills: string[];
  created_at: string;
  updated_at: string;
}

export interface EmergentSkill {
  id: string;
  name: string;
  description: string;
  description_it: string;
  trigger_patterns: string[];
  workflow_steps: Record<string, any>[];
  category: string;
  use_count: number;
  success_rate: number;
  enabled: boolean;
  tags: string[];
}

export interface MNEMEStats {
  total_entries: number;
  by_category: Record<string, number>;
  total_skills: number;
  enabled_skills: number;
  recent_activity: {
    title: string;
    category: string;
    date: string;
  }[];
}

// Skills
export interface Skill {
  name: string;
  description: string;
  description_it: string;
  type: 'god' | 'emergent';
  category: string;
  parameters: Record<string, any>;
  enabled: boolean;
  icon?: string;
}

export interface SkillResult {
  success: boolean;
  skill_name: string;
  result_type: string;
  data: any;
  error?: string;
  execution_time: number;
}

// Email
export interface EmailAccount {
  id: string;
  email: string;
  provider: string;
  display_name: string;
  is_active: boolean;
  unread_count?: number;
}

export interface Email {
  id: string;
  subject: string;
  from_address: string;
  from_name?: string;
  to_addresses: string[];
  body: string;
  body_html?: string;
  received_at: string;
  is_read: boolean;
  is_starred: boolean;
  labels: string[];
}

// API Responses
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// Dashboard
export interface DashboardStats {
  conversations_today: number;
  emails_processed: number;
  skills_executed: number;
  knowledge_entries: number;
  ai_tokens_used: number;
  active_integrations: number;
}
