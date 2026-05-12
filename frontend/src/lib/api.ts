// HTTP 客户端与各模块 API 封装
// 设计要点：
//   - 统一 baseURL，dev 走 vite 代理的 /api/v1，prod 走 VITE_API_BASE_URL
//   - 请求拦截器自动注入 Bearer access_token
//   - 响应拦截器在 401 时尝试 refresh 一次；并发 401 共享同一个刷新 Promise
//   - 刷新失败统一触发 triggerUnauthorized() 由上层清状态

import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  clearAllTokens,
  clearStoredProjectId,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "./authStorage";
import { triggerUnauthorized } from "./authEvents";
import type { AuditLogListResponse } from "@/types/audit";
import type {
  MeResponse,
  ProjectBrief,
  ProjectMemberRow,
} from "@/types/project";
import type {
  CreateTagData,
  Tag,
  TagListResponse,
  TagUpdateData,
} from "@/types/tag";
import type {
  CreateTicketData,
  Ticket,
  TicketListResponse,
  UpdateTicketData,
} from "@/types/ticket";

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const BASE_URL = RAW_BASE.trim() || "/api/v1";

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
  _skipAuth?: boolean;
}

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 20_000,
  headers: {
    Accept: "application/json",
  },
});

api.interceptors.request.use((config) => {
  const cfg = config as RetriableConfig;
  if (!cfg._skipAuth) {
    const token = getAccessToken();
    if (token) {
      cfg.headers = cfg.headers ?? {};
      cfg.headers.Authorization = `Bearer ${token}`;
    }
  }
  return cfg;
});

// 并发 401 时共享同一个 refresh Promise，避免触发限流或重复刷新
let refreshPromise: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const resp = await axios.post<TokenResponse>(
      `${BASE_URL}/auth/refresh`,
      { refresh_token: refresh },
      { timeout: 15_000 },
    );
    if (resp.data?.access_token && resp.data?.refresh_token) {
      setTokens(resp.data.access_token, resp.data.refresh_token);
      return resp.data.access_token;
    }
    return null;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (resp) => resp,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status;
    if (
      status === 401 &&
      original &&
      !original._retry &&
      !original._skipAuth
    ) {
      original._retry = true;
      if (!refreshPromise) {
        refreshPromise = performRefresh().finally(() => {
          refreshPromise = null;
        });
      }
      const newToken = await refreshPromise;
      if (newToken) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return api.request(original);
      }
      clearAllTokens();
      clearStoredProjectId();
      triggerUnauthorized();
    }
    return Promise.reject(error);
  },
);

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface UserPublic {
  id: number;
  username: string;
}

// ---------- auth ----------

export const authApi = {
  /** OAuth2 密码模式：使用 application/x-www-form-urlencoded 提交 */
  login: async (username: string, password: string): Promise<TokenResponse> => {
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);
    const cfg: AxiosRequestConfig = {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      _skipAuth: true,
    } as AxiosRequestConfig;
    const resp = await api.post<TokenResponse>("/auth/login", params, cfg);
    setTokens(resp.data.access_token, resp.data.refresh_token);
    return resp.data;
  },

  register: async (username: string, password: string): Promise<UserPublic> => {
    const cfg: AxiosRequestConfig = { _skipAuth: true } as AxiosRequestConfig;
    const resp = await api.post<UserPublic>(
      "/auth/register",
      { username, password },
      cfg,
    );
    return resp.data;
  },

  me: async (): Promise<MeResponse> => {
    const resp = await api.get<MeResponse>("/auth/me");
    return resp.data;
  },

  listUsers: async (): Promise<UserPublic[]> => {
    const resp = await api.get<UserPublic[]>("/auth/users");
    return resp.data;
  },

  changePassword: async (
    currentPassword: string,
    newPassword: string,
  ): Promise<void> => {
    await api.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};

// ---------- projects ----------

interface ProjectCreatePayload {
  name: string;
  description?: string;
}

interface ProjectUpdatePayload {
  name?: string;
  description?: string;
}

interface AddMemberPayload {
  user_id: number;
  role: string;
}

export const projectsApi = {
  list: async (): Promise<ProjectBrief[]> => {
    const resp = await api.get<ProjectBrief[]>("/projects");
    return resp.data;
  },

  get: async (projectId: number): Promise<ProjectBrief> => {
    const resp = await api.get<ProjectBrief>(`/projects/${projectId}`);
    return resp.data;
  },

  create: async (payload: ProjectCreatePayload): Promise<ProjectBrief> => {
    const resp = await api.post<ProjectBrief>("/projects", payload);
    return resp.data;
  },

  update: async (
    projectId: number,
    payload: ProjectUpdatePayload,
  ): Promise<ProjectBrief> => {
    const resp = await api.patch<ProjectBrief>(
      `/projects/${projectId}`,
      payload,
    );
    return resp.data;
  },

  delete: async (projectId: number): Promise<void> => {
    await api.delete(`/projects/${projectId}`);
  },

  listMembers: async (projectId: number): Promise<ProjectMemberRow[]> => {
    const resp = await api.get<ProjectMemberRow[]>(
      `/projects/${projectId}/members`,
    );
    return resp.data;
  },

  addMember: async (
    projectId: number,
    payload: AddMemberPayload,
  ): Promise<ProjectMemberRow> => {
    const resp = await api.post<ProjectMemberRow>(
      `/projects/${projectId}/members`,
      payload,
    );
    return resp.data;
  },

  removeMember: async (projectId: number, userId: number): Promise<void> => {
    await api.delete(`/projects/${projectId}/members/${userId}`);
  },

  workflowAssignees: async (projectId: number): Promise<UserPublic[]> => {
    const resp = await api.get<UserPublic[]>(
      `/projects/${projectId}/workflow-assignees`,
    );
    return resp.data;
  },
};

// ---------- tickets ----------

interface TicketListQuery {
  project_id: number;
  status?: string;
  tag_ids?: string;
  search?: string;
  created_by_user_id?: number;
  sort_by?: string;
  sort_order?: string;
  skip?: number;
  limit?: number;
}

interface WorkflowStepCompleteBody {
  completion_note?: string;
}

export const ticketApi = {
  list: async (params: TicketListQuery): Promise<TicketListResponse> => {
    const resp = await api.get<TicketListResponse>("/tickets", { params });
    return resp.data;
  },

  get: async (ticketId: number): Promise<Ticket> => {
    const resp = await api.get<Ticket>(`/tickets/${ticketId}`);
    return resp.data;
  },

  create: async (payload: CreateTicketData): Promise<Ticket> => {
    const resp = await api.post<Ticket>("/tickets", payload);
    return resp.data;
  },

  update: async (
    ticketId: number,
    payload: UpdateTicketData,
  ): Promise<Ticket> => {
    const resp = await api.put<Ticket>(`/tickets/${ticketId}`, payload);
    return resp.data;
  },

  delete: async (ticketId: number): Promise<void> => {
    await api.delete(`/tickets/${ticketId}`);
  },

  complete: async (ticketId: number): Promise<Ticket> => {
    const resp = await api.patch<Ticket>(`/tickets/${ticketId}/complete`);
    return resp.data;
  },

  uncomplete: async (ticketId: number): Promise<Ticket> => {
    const resp = await api.patch<Ticket>(`/tickets/${ticketId}/uncomplete`);
    return resp.data;
  },

  addTags: async (ticketId: number, tagIds: number[]): Promise<Ticket> => {
    const resp = await api.post<Ticket>(`/tickets/${ticketId}/tags`, tagIds);
    return resp.data;
  },

  removeTag: async (ticketId: number, tagId: number): Promise<void> => {
    await api.delete(`/tickets/${ticketId}/tags/${tagId}`);
  },

  completeWorkflowStep: async (
    ticketId: number,
    stepId: number,
    body: WorkflowStepCompleteBody,
  ): Promise<Ticket> => {
    const resp = await api.post<Ticket>(
      `/tickets/${ticketId}/workflow/steps/${stepId}/complete`,
      body,
    );
    return resp.data;
  },
};

// ---------- tags ----------

export const tagApi = {
  list: async (projectId: number): Promise<TagListResponse> => {
    const resp = await api.get<TagListResponse>("/tags", {
      params: { project_id: projectId },
    });
    return resp.data;
  },

  get: async (tagId: number): Promise<Tag> => {
    const resp = await api.get<Tag>(`/tags/${tagId}`);
    return resp.data;
  },

  create: async (payload: CreateTagData): Promise<Tag> => {
    const resp = await api.post<Tag>("/tags", payload);
    return resp.data;
  },

  update: async (tagId: number, payload: TagUpdateData): Promise<Tag> => {
    const resp = await api.patch<Tag>(`/tags/${tagId}`, payload);
    return resp.data;
  },

  delete: async (tagId: number): Promise<void> => {
    await api.delete(`/tags/${tagId}`);
  },
};

// ---------- audit ----------

interface AuditListQuery {
  project_id?: number;
  skip?: number;
  limit?: number;
}

export const auditApi = {
  list: async (params: AuditListQuery): Promise<AuditLogListResponse> => {
    const resp = await api.get<AuditLogListResponse>("/audit-logs", { params });
    return resp.data;
  },
};
