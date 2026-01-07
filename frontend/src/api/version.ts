import request from './request';

export interface Version {
    id: string;
    version: number;
    release_notes: string | null;
    published_by: string | null;
    published_by_username: string | null;
    published_at: string;
}

export interface VersionDetail extends Version {
    snapshot_jsonb: {
        version: number;
        published_at: string;
        entities: any[];
        relations: any[];
    };
}

export interface VersionListParams {
    page?: number;
    size?: number;
}

export interface VersionListResponse {
    items: Version[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface PublishParams {
    release_notes?: string;
}

export const versionApi = {
    list: (params: VersionListParams) => {
        return request.get<any, VersionListResponse>('/versions', { params });
    },

    publish: (data: PublishParams) => {
        return request.post<any, Version>('/versions/publish', data);
    },

    get: (id: string) => {
        return request.get<any, VersionDetail>(`/versions/${id}`);
    },

    copyToDraft: (id: string) => {
        return request.post<any, { message: string; entities_created: number; relations_created: number }>(
            `/versions/${id}/copy-to-draft`
        );
    },
};

// Import/Export API
export interface ImportResult {
    success: boolean;
    errors: Array<{
        sheet: string;
        row: number;
        field: string;
        value: string | null;
        error: string;
    }>;
    entities_count: number;
    relations_count: number;
    entity_properties_count: number;
    relation_properties_count: number;
}

export const importExportApi = {
    downloadTemplate: () => {
        return request.get('/import/template', { responseType: 'blob' });
    },

    importExcel: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return request.post<any, ImportResult>('/import/excel', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    exportJson: () => {
        return request.get('/import/json');
    },

    exportExcel: () => {
        return request.get('/import/excel', { responseType: 'blob' });
    },
};
