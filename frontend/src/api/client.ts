import axios from "axios";
import { UserIDManager } from "./userIdManager";
import type { UploadResponse, SearchResponse } from "../types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
    console.warn("VITE_API_BASE_URL is not set. API requests will fail.");
}

interface SessionResponse {
    user_id: string;
    session_active: boolean;
}

const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

// Request interceptor to add user ID to all requests via X-User-ID header
apiClient.interceptors.request.use(async (config) => {
    const userId = await UserIDManager.getOrCreateUserId();
    config.headers['X-User-ID'] = userId;
    return config;
});

// Get or create user ID
export const getSessionId = async (): Promise<string> => {
    return UserIDManager.getOrCreateUserId();
};

// Get current session info from backend
export const getCurrentSession = async (): Promise<SessionResponse> => {
    const response = await apiClient.get<SessionResponse>("/api/v1/session/");
    return response.data;
};

// Clear session (client-side only)
export const clearSession = () => {
    UserIDManager.clearUserId();
};

// Upload document (userId passed via X-User-ID header by interceptor)
export const uploadDocument = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post<UploadResponse>("/api/v1/ingest/", formData);
    return response.data;
};

// Search documents (userId passed via X-User-ID header by interceptor)
export const searchDocuments = async (query: string): Promise<SearchResponse> => {
    const response = await apiClient.post<SearchResponse>("/api/v1/search/", {
        query,
        top_k: 4,
    });
    return response.data;
};