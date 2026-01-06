import request from './request';

export interface LoginParams {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface User {
    id: string;
    username: string;
    role: 'ADMIN' | 'USER';
    is_active: boolean;
}

export const authApi = {
    login: (data: LoginParams) => {
        return request.post<any, TokenResponse>('/auth/login', data);
    },

    refresh: (refresh_token: string) => {
        return request.post<any, TokenResponse>('/auth/refresh', { refresh_token });
    },

    me: () => {
        return request.get<any, User>('/auth/me');
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
    },
};
