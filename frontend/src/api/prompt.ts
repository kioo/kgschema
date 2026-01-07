/**
 * Prompt API service with version management.
 */
import request from './request';

// ===== Types =====

export interface Prompt {
    id: string;
    tag: string;
    content: string;
    description: string | null;
    current_version: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface PromptVersion {
    id: string;
    prompt_id: string;
    version: number;
    content: string;
    description: string | null;
    change_note: string | null;
    created_at: string;
}

export interface PromptDetail extends Prompt {
    versions: PromptVersion[];
}

export interface PromptListResponse {
    items: Prompt[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface PromptVersionListResponse {
    items: PromptVersion[];
    total: number;
}

export interface PromptCreateParams {
    tag: string;
    content: string;
    description?: string;
}

export interface PromptUpdateParams {
    content?: string;
    description?: string;
    create_version?: boolean;
    change_note?: string;
}

// ===== API Functions =====

export const promptApi = {
    /**
     * List all prompts with pagination.
     */
    list: async (page = 1, size = 20, search?: string): Promise<PromptListResponse> => {
        const params = new URLSearchParams({ page: String(page), size: String(size) });
        if (search) params.append('search', search);
        return request.get(`/prompts?${params}`);
    },

    /**
     * Get prompt details with version history.
     */
    get: async (id: string): Promise<PromptDetail> => {
        return request.get(`/prompts/${id}`);
    },

    /**
     * Create a new prompt.
     */
    create: async (data: PromptCreateParams): Promise<Prompt> => {
        return request.post('/prompts', data);
    },

    /**
     * Update a prompt.
     */
    update: async (id: string, data: PromptUpdateParams): Promise<Prompt> => {
        return request.patch(`/prompts/${id}`, data);
    },

    /**
     * Delete a prompt (soft delete).
     */
    delete: async (id: string): Promise<void> => {
        return request.delete(`/prompts/${id}`);
    },

    /**
     * Get all versions of a prompt.
     */
    getVersions: async (promptId: string): Promise<PromptVersionListResponse> => {
        return request.get(`/prompts/${promptId}/versions`);
    },

    /**
     * Get a specific version.
     */
    getVersion: async (promptId: string, version: number): Promise<PromptVersion> => {
        return request.get(`/prompts/${promptId}/versions/${version}`);
    },

    /**
     * Rollback to a specific version.
     */
    rollback: async (promptId: string, version: number): Promise<Prompt> => {
        return request.post(`/prompts/${promptId}/rollback/${version}`);
    },
};
