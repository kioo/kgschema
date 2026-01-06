import axios from 'axios';
import { message } from 'antd';

// 创建 axios 实例
const request = axios.create({
    baseURL: '/api/v1',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器
request.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
request.interceptors.response.use(
    (response) => {
        return response.data;
    },
    async (error) => {
        const originalRequest = error.config;

        // 处理 401 (未授权)
        if (error.response?.status === 401 && !originalRequest._retry) {
            const refreshToken = localStorage.getItem('refresh_token');

            if (refreshToken) {
                originalRequest._retry = true;

                try {
                    // 尝试刷新 token
                    // 注意：为了避免循环依赖，这里直接使用 axios 而不是 request 实例
                    // 并且你需要确保刷新接口路径正确
                    const response = await axios.post('/api/v1/auth/refresh', {
                        refresh_token: refreshToken,
                    });

                    const { access_token, refresh_token: new_refresh_token } = response.data;

                    localStorage.setItem('access_token', access_token);
                    localStorage.setItem('refresh_token', new_refresh_token);

                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return request(originalRequest);
                } catch (refreshError) {
                    // 刷新失败，清除 token 并跳转登录
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                    message.error('登录已过期，请重新登录');
                    return Promise.reject(refreshError);
                }
            } else {
                // 没有 refresh token，直接跳登录
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                    message.error('请先登录');
                }
            }
        } else if (error.response?.data?.detail) {
            message.error(error.response.data.detail);
        } else {
            message.error('网络请求失败');
        }

        return Promise.reject(error);
    }
);

export default request;
