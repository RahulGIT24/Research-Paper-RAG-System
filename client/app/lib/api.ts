import axios from 'axios'

export const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    withCredentials: true
})

let isRefreshing = false;
let failedQueue: {
    resolve: (value?: unknown) => void;
    reject: (value?: unknown) => void;
}[] = []

const processQueue = (error: unknown = null) => {
    failedQueue.forEach((promise) => {
        if (error) {
            promise.reject(error);
        } else {
            promise.resolve()
        }
    });
    failedQueue = []
}

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status !== 401 || originalRequest._retry) {
            return Promise.reject(error);
        }
        originalRequest._retry = true;
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then(() => api(originalRequest));
        }
        isRefreshing = true;
        try {
            await api.post("/auth/refresh");

            processQueue();

            return api(originalRequest);
        } catch (err) {
            processQueue(err);

            window.location.href = "/signin";

            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);