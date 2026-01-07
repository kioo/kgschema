import request from './request';

export interface RelationProperty {
    id: string;
    relation_id: string;
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

export interface Relation {
    id: string;
    relation_code: string;
    relation_name: string;
    relation_name_en: string | null;
    head_entity_id: string;
    tail_entity_id: string;
    head_entity_code: string | null;
    tail_entity_code: string | null;
    description: string | null;
    status: 'DRAFT' | 'ACTIVE';
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface RelationDetail extends Relation {
    properties: RelationProperty[];
}

export interface RelationListParams {
    page?: number;
    size?: number;
    status?: 'DRAFT' | 'ACTIVE';
    is_active?: boolean;
    search?: string;
}

export interface RelationListResponse {
    items: Relation[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface RelationCreateParams {
    relation_code: string;
    relation_name: string;
    relation_name_en?: string;
    head_entity_id: string;
    tail_entity_id: string;
    description?: string;
}

export interface RelationUpdateParams {
    relation_name?: string;
    relation_name_en?: string;
    head_entity_id?: string;
    tail_entity_id?: string;
    description?: string;
    status?: 'DRAFT' | 'ACTIVE';
}

export interface RelationPropertyCreateParams {
    prop_code: string;
    prop_name: string;
    prop_name_en?: string;
    data_type?: string;
    options_json?: string[];
    is_required?: boolean;
    display_order?: number;
}

export interface RelationPropertyUpdateParams {
    prop_name?: string;
    prop_name_en?: string;
    data_type?: string;
    options_json?: string[];
    is_required?: boolean;
    display_order?: number;
}

export const relationApi = {
    list: (params: RelationListParams) => {
        return request.get<any, RelationListResponse>('/relations', { params });
    },

    create: (data: RelationCreateParams) => {
        return request.post<any, Relation>('/relations', data);
    },

    get: (id: string) => {
        return request.get<any, RelationDetail>(`/relations/${id}`);
    },

    update: (id: string, data: RelationUpdateParams) => {
        return request.patch<any, Relation>(`/relations/${id}`, data);
    },

    delete: (id: string) => {
        return request.delete(`/relations/${id}`);
    },

    // Properties
    listProperties: (relationId: string) => {
        return request.get<any, RelationProperty[]>(`/relations/${relationId}/properties`);
    },

    createProperty: (relationId: string, data: RelationPropertyCreateParams) => {
        return request.post<any, RelationProperty>(`/relations/${relationId}/properties`, data);
    },

    updateProperty: (relationId: string, propId: string, data: RelationPropertyUpdateParams) => {
        return request.patch<any, RelationProperty>(`/relations/${relationId}/properties/${propId}`, data);
    },

    deleteProperty: (relationId: string, propId: string) => {
        return request.delete(`/relations/${relationId}/properties/${propId}`);
    },
};
