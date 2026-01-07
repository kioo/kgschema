import request from './request';

export interface EntityProperty {
    id: string;
    entity_id: string;
    prop_code: string;
    prop_name: string;
    prop_name_en: string | null;
    data_type: string;
    options_json: string[] | null;
    is_required: boolean;
    display_order: number;
    created_at: string;
    updated_at: string;
}

export interface Entity {
    id: string;
    entity_code: string;
    entity_name: string;
    entity_name_en: string | null;
    description: string | null;
    status: 'DRAFT' | 'ACTIVE';
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface EntityDetail extends Entity {
    properties: EntityProperty[];
}

export interface EntityListParams {
    page?: number;
    size?: number;
    status?: 'DRAFT' | 'ACTIVE';
    is_active?: boolean;
    search?: string;
}

export interface EntityListResponse {
    items: Entity[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface EntityCreateParams {
    entity_code: string;
    entity_name: string;
    entity_name_en?: string;
    description?: string;
}

export interface EntityUpdateParams {
    entity_name?: string;
    entity_name_en?: string;
    description?: string;
    status?: 'DRAFT' | 'ACTIVE';
}

export interface PropertyCreateParams {
    prop_code: string;
    prop_name: string;
    prop_name_en?: string;
    data_type?: string;
    options_json?: string[];
    is_required?: boolean;
    display_order?: number;
}

export interface PropertyUpdateParams {
    prop_name?: string;
    prop_name_en?: string;
    data_type?: string;
    options_json?: string[];
    is_required?: boolean;
    display_order?: number;
}

export const entityApi = {
    list: (params: EntityListParams) => {
        return request.get<any, EntityListResponse>('/entities', { params });
    },

    create: (data: EntityCreateParams) => {
        return request.post<any, Entity>('/entities', data);
    },

    get: (id: string) => {
        return request.get<any, EntityDetail>(`/entities/${id}`);
    },

    update: (id: string, data: EntityUpdateParams) => {
        return request.patch<any, Entity>(`/entities/${id}`, data);
    },

    delete: (id: string) => {
        return request.delete(`/entities/${id}`);
    },

    // Properties
    listProperties: (entityId: string) => {
        return request.get<any, EntityProperty[]>(`/entities/${entityId}/properties`);
    },

    createProperty: (entityId: string, data: PropertyCreateParams) => {
        return request.post<any, EntityProperty>(`/entities/${entityId}/properties`, data);
    },

    updateProperty: (entityId: string, propId: string, data: PropertyUpdateParams) => {
        return request.patch<any, EntityProperty>(`/entities/${entityId}/properties/${propId}`, data);
    },

    deleteProperty: (entityId: string, propId: string) => {
        return request.delete(`/entities/${entityId}/properties/${propId}`);
    },
};
