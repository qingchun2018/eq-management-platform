import { create } from "zustand";
import { authApi } from "@/lib/api";
import {
  clearAllTokens,
  clearStoredProjectId,
  getAccessToken,
  getStoredProjectId,
  setStoredProjectId,
} from "@/lib/authStorage";
import type { MeResponse, ProjectBrief } from "@/types/project";
import {
  roleCanManageMembers,
  roleCanManageTags,
  roleCanWriteTicket,
} from "@/types/project";

type AuthState = {
  username: string | null;
  /** 当前用户信息（含小组、项目列表） */
  me: MeResponse | null;
  /** 当前选中的项目 ID，与票据/标签请求一致 */
  currentProjectId: number | null;
  isReady: boolean;
  bootstrap: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** 切换项目并写入本地 */
  setCurrentProjectId: (id: number) => void;
  /** 登录后或需要刷新权限时调用 */
  refreshMe: () => Promise<void>;
  /** 当前项目下的角色字符串，无项目时为 null */
  currentProjectRole: () => string | null;
  canWriteInCurrentProject: () => boolean;
  canManageTagsInCurrentProject: () => boolean;
  canManageMembersInCurrentProject: () => boolean;
  isTeamAdmin: () => boolean;
};

function pickInitialProjectId(projects: ProjectBrief[]): number | null {
  if (projects.length === 0) return null;
  const stored = getStoredProjectId();
  if (stored !== null && projects.some((p) => p.id === stored)) {
    return stored;
  }
  return projects[0].id;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  username: null,
  me: null,
  currentProjectId: null,
  isReady: false,

  currentProjectRole: () => {
    const { me, currentProjectId } = get();
    if (!me || currentProjectId === null) return null;
    const p = me.projects.find((x) => x.id === currentProjectId);
    return p?.my_role ?? null;
  },

  canWriteInCurrentProject: () =>
    roleCanWriteTicket(get().currentProjectRole()),

  canManageTagsInCurrentProject: () =>
    roleCanManageTags(get().currentProjectRole()),

  canManageMembersInCurrentProject: () =>
    roleCanManageMembers(get().currentProjectRole()),

  isTeamAdmin: () => get().me?.team_role === "TEAM_ADMIN",

  setCurrentProjectId: (id: number) => {
    setStoredProjectId(id);
    set({ currentProjectId: id });
  },

  refreshMe: async () => {
    const me = await authApi.me();
    const pid = pickInitialProjectId(me.projects);
    if (pid !== null) setStoredProjectId(pid);
    set({
      me,
      username: me.username,
      currentProjectId: pid,
    });
  },

  bootstrap: async () => {
    const token = getAccessToken();
    if (!token) {
      set({ isReady: true, username: null, me: null, currentProjectId: null });
      return;
    }
    try {
      await get().refreshMe();
      set({ isReady: true });
    } catch {
      clearAllTokens();
      clearStoredProjectId();
      set({
        username: null,
        me: null,
        currentProjectId: null,
        isReady: true,
      });
    }
  },

  login: async (username: string, password: string) => {
    await authApi.login(username, password);
    await get().refreshMe();
  },

  register: async (username: string, password: string) => {
    await authApi.register(username, password);
    await get().login(username, password);
  },

  logout: () => {
    clearAllTokens();
    clearStoredProjectId();
    set({ username: null, me: null, currentProjectId: null });
  },
}));
