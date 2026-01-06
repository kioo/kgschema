import request from './request';
import type { User } from './auth';

export interface UserListParams {
    page?: number;
    size?: number;
}

export interface UserListResponse {
    items: User[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface CreateUserParams {
    username: string;
    password: string;
    role: 'ADMIN' | 'USER';
}

export interface UpdateUserParams {
    role?: 'ADMIN' | 'USER';
    is_active?: boolean;
}

export const userApi = {
    list: (params: UserListParams) => {
        return request.get<any, UserListResponse>('/users', { params });
    },

    create: (data: CreateUserParams) => {
        return request.post<any, User>('/users', data);
    },

    update: (id: string, data: UpdateUserParams) => {
        return request.patch<any, User>(`/users/${id}`, data);
    },

    get: (id: string) => {
        return request.get<any, User>(`/users/${id}`);
    },

    resetPassword: (id: string, new_password: string) => {
        return request.post<any, { detail: string }>(`/users/${id}/reset-password`, { new_password });
    },
};
