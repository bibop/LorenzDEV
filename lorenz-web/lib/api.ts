/**
 * LORENZ SaaS - API Client
 * Centralized API communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface FetchOptions extends RequestInit {
  timeout?: number;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('lorenz_token', token);
      } else {
        localStorage.removeItem('lorenz_token');
      }
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      return localStorage.getItem('lorenz_token');
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: FetchOptions = {}
  ): Promise<T> {
    const { timeout = 30000, ...fetchOptions } = options;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    const token = this.getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          error.detail || `HTTP ${response.status}`,
          response.status,
          error
        );
      }

      return response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if ((error as Error).name === 'AbortError') {
        throw new ApiError('Request timeout', 408);
      }
      throw new ApiError((error as Error).message, 500);
    }
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.request<{ access_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  async register(data: { email: string; password: string; full_name: string }) {
    return this.request<{ access_token: string; user: any }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        email: data.email,
        password: data.password,
        name: data.full_name,
      }),
    });
  }

  async logout() {
    this.setToken(null);
  }

  async getCurrentUser() {
    return this.request<any>('/users/me');
  }

  async updateUserPreferences(preferences: {
    assistant_name?: string;
    assistant_birth_date?: string;
    assistant_zodiac?: string;
    assistant_ascendant?: string;
    theme?: string;
    language?: string;
  }) {
    return this.request<any>('/users/me/preferences', {
      method: 'PATCH',
      body: JSON.stringify(preferences),
    });
  }

  async completeOnboarding() {
    return this.request<any>('/users/me/onboarding/complete', {
      method: 'POST',
    });
  }

  // Chat endpoints
  async sendMessage(message: string, conversationId?: string) {
    return this.request<any>('/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });
  }

  async getConversations(limit = 50) {
    return this.request<any[]>(`/chat/conversations?limit=${limit}`);
  }

  async getConversation(id: string) {
    return this.request<any>(`/chat/conversations/${id}`);
  }

  // Knowledge endpoints (MNEME)
  async getKnowledgeEntries(category?: string, limit = 50) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    params.set('limit', limit.toString());
    return this.request<any[]>(`/knowledge/entries?${params}`);
  }

  async createKnowledgeEntry(data: {
    category: string;
    title: string;
    content: string;
    tags?: string[];
    context?: Record<string, any>;
  }) {
    return this.request<any>('/knowledge/entries', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async searchKnowledge(query: string, options?: {
    category?: string;
    semantic?: boolean;
    limit?: number;
  }) {
    return this.request<any[]>('/knowledge/entries/search', {
      method: 'POST',
      body: JSON.stringify({ query, ...options }),
    });
  }

  async getMNEMEStats() {
    return this.request<any>('/knowledge/stats');
  }

  async getEmergentSkills(enabledOnly = true) {
    return this.request<any[]>(`/knowledge/skills?enabled_only=${enabledOnly}`);
  }

  async quickRemember(title: string, content: string, category = 'fact') {
    return this.request<any>(`/knowledge/remember?title=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}&category=${category}`, {
      method: 'POST',
    });
  }

  // Skills endpoints
  async getSkills() {
    return this.request<any[]>('/skills');
  }

  async executeSkill(skillName: string, parameters: Record<string, any>) {
    return this.request<any>('/skills/execute', {
      method: 'POST',
      body: JSON.stringify({ skill_name: skillName, parameters }),
    });
  }

  async autoExecuteSkill(userRequest: string) {
    return this.request<any>('/skills/auto-execute', {
      method: 'POST',
      body: JSON.stringify({ user_request: userRequest }),
    });
  }

  // Email endpoints
  async getEmailAccounts() {
    return this.request<any[]>('/email/accounts');
  }

  async getEmails(accountId: string, limit = 50) {
    return this.request<any[]>(`/email/${accountId}/messages?limit=${limit}`);
  }

  async sendEmail(data: {
    from_account_id: string;
    to: string[];
    subject: string;
    body: string;
  }) {
    return this.request<any>('/email/send', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // RAG endpoints
  async queryRAG(query: string, options?: {
    top_k?: number;
    use_reranking?: boolean;
    source_types?: string[];
  }) {
    return this.request<any>('/rag/query', {
      method: 'POST',
      body: JSON.stringify({ query, ...options }),
    });
  }

  async searchRAG(query: string, options?: {
    source_types?: string[];
    limit?: number;
    use_reranking?: boolean;
  }) {
    return this.request<{
      results: Array<{
        doc_id: string;
        title: string;
        content: string;
        score: number;
        source: string;
        metadata: Record<string, any>;
      }>;
      total: number;
      query: string;
    }>('/rag/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit: options?.limit || 10,
        source_types: options?.source_types,
        use_reranking: options?.use_reranking ?? true,
      }),
    });
  }

  async getRAGDocuments(options?: {
    source_type?: string;
    limit?: number;
    offset?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.source_type) params.set('source_type', options.source_type);
    if (options?.limit) params.set('limit', options.limit.toString());
    if (options?.offset) params.set('offset', options.offset.toString());
    return this.request<{
      documents: Array<{
        id: string;
        title: string;
        source_type: string;
        total_chunks: number;
        status: string;
        metadata: Record<string, any>;
        created_at: string;
      }>;
      total: number;
      has_more: boolean;
    }>(`/rag/documents?${params}`);
  }

  async uploadDocument(file: File): Promise<{
    document_id: string;
    filename: string;
    status: string;
    message: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/rag/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(error.detail || 'Upload failed', response.status);
    }

    return response.json();
  }

  async uploadDocumentsBatch(files: File[]): Promise<{
    uploaded: number;
    failed: number;
    documents: Array<{
      document_id: string;
      filename: string;
      status: string;
      message: string;
    }>;
  }> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const token = this.getToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/rag/documents/upload/batch`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(error.detail || 'Batch upload failed', response.status);
    }

    return response.json();
  }

  async indexText(data: {
    title: string;
    content: string;
    source_type?: string;
    metadata?: Record<string, any>;
  }) {
    return this.request<{
      document_id: string;
      title: string;
      status: string;
      content_length: number;
    }>('/rag/documents/index-text', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteRAGDocument(documentId: string) {
    return this.request<{ message: string; document_id: string }>(`/rag/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async getRAGStats() {
    return this.request<{
      total_documents: number;
      total_chunks: number;
      sources: Record<string, number>;
      vector_indexed: number;
      embedding_model: string;
      reranker_enabled: boolean;
    }>('/rag/stats');
  }

  async getRAGSupportedFormats() {
    return this.request<{
      extensions: string[];
      content_types: string[];
      max_file_size_mb: number;
      max_batch_files: number;
      features: {
        pdf_ocr: boolean;
        image_ocr: boolean;
        office_documents: boolean;
        spreadsheets: boolean;
        presentations: boolean;
      };
    }>('/rag/formats');
  }

  // Twin endpoints (Human Digital Twin)
  async getTwinProfile() {
    return this.request<any>('/twin/profile');
  }

  async updateTwinProfile(updates: {
    preferred_name?: string;
    twin_name?: string;
    autonomy_level?: number;
    communication_style?: string;
    languages?: string[];
  }) {
    return this.request<any>('/twin/profile', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async getVIPContacts() {
    return this.request<any>('/twin/profile/vip');
  }

  async addVIPContact(email: string) {
    return this.request<any>('/twin/profile/vip', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async removeVIPContact(email: string) {
    return this.request<any>(`/twin/profile/vip/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });
  }

  async getTwinProjects(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request<any>(`/twin/projects${params}`);
  }

  async addTwinProject(data: {
    name: string;
    description: string;
    priority?: number;
    keywords?: string[];
  }) {
    return this.request<any>('/twin/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTwinLearningStats() {
    return this.request<any>('/twin/learning/stats');
  }

  async getTwinPatterns(limit = 20) {
    return this.request<any>(`/twin/learning/patterns?limit=${limit}`);
  }

  async getTwinSuggestions() {
    return this.request<any>('/twin/suggestions');
  }

  async getDailyBriefing(pendingEmails = 0) {
    return this.request<any>('/twin/briefing/daily', {
      method: 'POST',
      body: JSON.stringify({ pending_emails: pendingEmails }),
    });
  }

  async recordTwinFeedback(feedbackType: 'approved' | 'rejected' | 'modified', data: Record<string, any>) {
    return this.request<any>('/twin/feedback', {
      method: 'POST',
      body: JSON.stringify({ feedback_type: feedbackType, data }),
    });
  }

  // Twin Email Integration endpoints
  async twinAnalyzeEmail(data: {
    from: string;
    subject: string;
    body: string;
    message_id?: string;
  }) {
    return this.request<any>('/email/twin/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async twinDraftResponse(data: {
    original_from: string;
    original_subject: string;
    original_body: string;
    intent?: string;
  }) {
    return this.request<any>('/email/twin/draft', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async twinSmartInbox(accountId?: string, limit = 50) {
    return this.request<{
      categorized: {
        critical: any[];
        high: any[];
        medium: any[];
        low: any[];
      };
      stats: {
        critical: number;
        high: number;
        medium: number;
        low: number;
        total: number;
      };
      vip_count: number;
      active_projects: number;
    }>('/email/twin/smart-inbox', {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, limit }),
    });
  }

  async twinBatchAnalyze(accountId?: string, limit = 20) {
    return this.request<{
      analyzed: number;
      results: Array<{
        message_id: string;
        from: string;
        subject: string;
        priority: string;
        actions: string[];
        is_vip: boolean;
      }>;
    }>('/email/twin/batch-analyze', {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, limit }),
    });
  }

  // Email RAG Indexing
  async indexEmailsToRAG(accountId?: string, limit = 50) {
    return this.request<{
      message: string;
      indexed: number;
      skipped: number;
      errors: number;
    }>('/email/index-to-rag', {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, limit }),
    });
  }

  // ==========================================================================
  // AUTO-SETUP / ONBOARDING ENDPOINTS
  // ==========================================================================

  async startAutoSetup(options?: {
    include_local_scan?: boolean;
    include_cloud?: boolean;
    include_social?: boolean;
  }) {
    return this.request<{
      session_id: string;
      progress: SetupProgress;
      next_step: SetupStep | null;
      required_oauth_providers: string[];
    }>('/onboarding/auto-setup/start', {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  }

  async getAutoSetupProgress() {
    return this.request<{
      progress: SetupProgress | null;
      next_step: SetupStep | null;
      required_oauth_providers: string[];
    }>('/onboarding/auto-setup/progress');
  }

  async executeSetupStep(stepId: string, oauthTokens?: Record<string, string>) {
    return this.request<{
      step: SetupStep;
      progress: SetupProgress;
      next_step: SetupStep | null;
    }>('/onboarding/auto-setup/execute-step', {
      method: 'POST',
      body: JSON.stringify({
        step_id: stepId,
        oauth_tokens: oauthTokens,
      }),
    });
  }

  async skipSetupStep(stepId: string) {
    return this.request<{
      step: SetupStep;
      progress: SetupProgress;
      next_step: SetupStep | null;
    }>(`/onboarding/auto-setup/skip-step/${stepId}`, {
      method: 'POST',
    });
  }

  async completeAutoSetup() {
    return this.request<{
      message: string;
      final_progress: SetupProgress | null;
    }>('/onboarding/auto-setup/complete', {
      method: 'POST',
    });
  }

  async quickSystemScan() {
    return this.request<{
      platform: string;
      home_dir: string;
      directories_available: string[];
      email_clients_detected: string[];
      calendar_sources_detected: string[];
      estimated_scan_dirs: number;
    }>('/onboarding/discovery/quick-scan');
  }

  async discoverCloudStorage(provider: string, accessToken: string, maxFiles = 500) {
    return this.request<{
      scan_id: string;
      provider: string;
      files_found: number;
      folders_found: number;
      total_size_mb: number;
      files_preview: any[];
      errors: string[];
    }>('/onboarding/discovery/cloud', {
      method: 'POST',
      body: JSON.stringify({
        provider,
        access_token: accessToken,
        max_files: maxFiles,
      }),
    });
  }

  async ingestSocialHistory(platform: string, accessToken: string, maxPosts = 100) {
    return this.request<{
      scan_id: string;
      platform: string;
      profile: any;
      experiences_count: number;
      education_count: number;
      skills_count: number;
      content_count: number;
      interests: string[];
      summary: Record<string, any>;
      errors: string[];
    }>('/onboarding/discovery/social', {
      method: 'POST',
      body: JSON.stringify({
        platform,
        access_token: accessToken,
        max_posts: maxPosts,
      }),
    });
  }

  // OAuth URL getters
  getOAuthUrl(provider: string): string {
    return `${API_BASE_URL}/auth/oauth/${provider}`;
  }

  // Generic POST method for custom endpoints
  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // Generic GET method for custom endpoints
  async get<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }
}

// Type definitions for setup
export interface SetupStep {
  id: string;
  phase: string;
  title: string;
  description: string;
  priority: 'required' | 'recommended' | 'optional';
  requires_oauth: boolean;
  oauth_provider: string | null;
  oauth_scopes: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'skipped' | 'failed';
  result: any | null;
  error: string | null;
}

export interface SetupProgress {
  session_id: string;
  user_id: string;
  current_phase: string;
  current_step_id: string | null;
  steps: SetupStep[];
  started_at: string;
  updated_at: string;
  completed_at: string | null;
  percent_complete: number;
  discoveries: Record<string, any>;
}

// Custom error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Singleton instance
export const api = new ApiClient();
export default api;
