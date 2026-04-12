import { create } from "zustand";
import { toast } from "sonner";
import { ticketApi, tagApi, authApi } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import type {
  Ticket,
  CreateTicketData,
  UpdateTicketData,
} from "@/types/ticket";
import type { Tag } from "@/types/tag";

type SortField = "created_at" | "updated_at" | "title";
type SortOrder = "asc" | "desc";

export type FilterUser = { id: number; username: string };

function axiosDetail(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const d = (err as { response?: { data?: { detail?: unknown } } }).response?.data
      ?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((item: { msg?: string }) => (typeof item?.msg === "string" ? item.msg : String(item)))
        .join("; ");
    }
  }
  return "";
}

interface TicketStore {
  tickets: Ticket[];
  tags: Tag[];
  filterUsers: FilterUser[];
  isLoading: boolean;
  error: string | null;

  statusFilter: "all" | "pending" | "completed";
  selectedTagIds: number[];
  searchQuery: string;
  sortField: SortField;
  sortOrder: SortOrder;
  filterUserId: number | null;
  page: number;
  pageSize: number;
  total: number;

  fetchTickets: () => Promise<void>;
  fetchTags: () => Promise<void>;
  fetchFilterUsers: () => Promise<void>;
  createTicket: (data: Omit<CreateTicketData, "project_id">) => Promise<void>;
  updateTicket: (id: number, data: UpdateTicketData) => Promise<void>;
  deleteTicket: (id: number) => Promise<void>;
  toggleComplete: (id: number) => Promise<void>;
  /** 完成工作流中当前步骤并流转给下一位 */
  completeWorkflowStep: (
    ticketId: number,
    stepId: number,
    completionNote?: string,
  ) => Promise<void>;
  batchComplete: (ids: number[]) => Promise<void>;
  batchDelete: (ids: number[]) => Promise<void>;

  createTag: (data: { name: string; color?: string }) => Promise<void>;
  updateTag: (id: number, data: { name?: string; color?: string }) => Promise<void>;
  deleteTag: (id: number) => Promise<void>;
  addTagToTicket: (ticketId: number, tagIds: number[]) => Promise<void>;
  removeTagFromTicket: (ticketId: number, tagId: number) => Promise<void>;

  setStatusFilter: (status: "all" | "pending" | "completed") => void;
  setSelectedTagIds: (ids: number[]) => void;
  setSearchQuery: (query: string) => void;
  setSortField: (field: SortField) => void;
  setSortOrder: (order: SortOrder) => void;
  setFilterUserId: (userId: number | null) => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;

  /** 切换项目时重置所有筛选条件 */
  resetFilters: () => void;
  reset: () => void;
}

export const useTicketStore = create<TicketStore>((set, get) => ({
  tickets: [],
  tags: [],
  filterUsers: [],
  isLoading: false,
  error: null,
  statusFilter: "all",
  selectedTagIds: [],
  searchQuery: "",
  sortField: "created_at",
  sortOrder: "desc",
  filterUserId: null,
  page: 1,
  pageSize: 10,
  total: 0,

  fetchTickets: async () => {
    const projectId = useAuthStore.getState().currentProjectId;
    if (projectId === null) {
      set({ tickets: [], total: 0, isLoading: false, error: null });
      return;
    }
    set({ isLoading: true, error: null });
    try {
      const {
        statusFilter,
        selectedTagIds,
        searchQuery,
        sortField,
        sortOrder,
        page,
        pageSize,
        filterUserId,
      } = get();
      const skip = (page - 1) * pageSize;
      const response = await ticketApi.list({
        project_id: projectId,
        status: statusFilter,
        tag_ids:
          selectedTagIds.length > 0 ? selectedTagIds.join(",") : undefined,
        search: searchQuery || undefined,
        created_by_user_id: filterUserId ?? undefined,
        sort_by: sortField,
        sort_order: sortOrder,
        skip,
        limit: pageSize,
      });
      set({
        tickets: response.tickets,
        total: response.total,
        isLoading: false,
      });
    } catch (error) {
      const detail = axiosDetail(error);
      set({
        error: detail || "加载 Ticket 失败",
        isLoading: false,
      });
    }
  },

  fetchTags: async () => {
    const projectId = useAuthStore.getState().currentProjectId;
    if (projectId === null) {
      set({ tags: [] });
      return;
    }
    try {
      const response = await tagApi.list(projectId);
      set({ tags: response.tags });
    } catch (error) {
      const detail = axiosDetail(error);
      toast.error(detail || "标签列表加载失败");
    }
  },

  fetchFilterUsers: async () => {
    try {
      const users = await authApi.listUsers();
      set({ filterUsers: users });
    } catch (error) {
      const detail = axiosDetail(error);
      toast.error(detail || "用户列表加载失败");
    }
  },

  createTicket: async (data) => {
    const projectId = useAuthStore.getState().currentProjectId;
    if (projectId === null) {
      set({ error: "请先选择项目", isLoading: false });
      throw new Error("请先选择项目");
    }
    set({ isLoading: true, error: null });
    try {
      const payload: CreateTicketData = { ...data, project_id: projectId };
      await ticketApi.create(payload);
      await get().fetchTickets();
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "创建 Ticket 失败", isLoading: false });
      throw error;
    }
  },

  updateTicket: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      await ticketApi.update(id, data);
      await get().fetchTickets();
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "更新 Ticket 失败", isLoading: false });
      throw error;
    }
  },

  deleteTicket: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await ticketApi.delete(id);
      await get().fetchTickets();
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "删除 Ticket 失败", isLoading: false });
      throw error;
    }
  },

  toggleComplete: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const ticket = get().tickets.find((t) => t.id === id);
      if (ticket) {
        if (ticket.workflow_steps && ticket.workflow_steps.length > 0) {
          if (ticket.status === "pending") {
            toast.error("此 Ticket 已启用顺序工作流，请使用卡片上的「完成本步」依次推进");
            set({ isLoading: false });
            return;
          }
          toast.error("工作流型 Ticket 不支持一键取消完成");
          set({ isLoading: false });
          return;
        }
        if (ticket.status === "pending") {
          await ticketApi.complete(id);
        } else {
          await ticketApi.uncomplete(id);
        }
        await get().fetchTickets();
      }
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "更新状态失败", isLoading: false });
      throw error;
    }
  },

  completeWorkflowStep: async (ticketId, stepId, completionNote) => {
    set({ isLoading: true, error: null });
    try {
      await ticketApi.completeWorkflowStep(ticketId, stepId, {
        completion_note: completionNote,
      });
      await get().fetchTickets();
      toast.success("本步已完成");
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "完成步骤失败", isLoading: false });
      toast.error(detail || "完成步骤失败");
      throw error;
    }
  },

  batchComplete: async (ids) => {
    set({ isLoading: true, error: null });
    try {
      const { tickets } = get();
      const safeIds = ids.filter((id) => {
        const t = tickets.find((x) => x.id === id);
        return t && (!t.workflow_steps || t.workflow_steps.length === 0);
      });
      if (safeIds.length < ids.length) {
        toast.info("已跳过含工作流的 Ticket，请在工作流中逐步完成");
      }
      await Promise.all(safeIds.map((id) => ticketApi.complete(id)));
      await get().fetchTickets();
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "批量完成失败", isLoading: false });
      throw error;
    }
  },

  batchDelete: async (ids) => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all(ids.map((id) => ticketApi.delete(id)));
      await get().fetchTickets();
      set({ isLoading: false });
    } catch (error) {
      const detail = axiosDetail(error);
      set({ error: detail || "批量删除失败", isLoading: false });
      throw error;
    }
  },

  createTag: async (data) => {
    const projectId = useAuthStore.getState().currentProjectId;
    if (projectId === null) {
      throw new Error("请先选择项目");
    }
    try {
      await tagApi.create({ ...data, project_id: projectId });
      await get().fetchTags();
    } catch (error) {
      console.error("Error creating tag:", error);
      throw error;
    }
  },

  updateTag: async (id, data) => {
    try {
      await tagApi.update(id, data);
      await get().fetchTags();
      await get().fetchTickets();
    } catch (error) {
      console.error("Error updating tag:", error);
      throw error;
    }
  },

  deleteTag: async (id) => {
    try {
      await tagApi.delete(id);
      await get().fetchTags();
      await get().fetchTickets();
    } catch (error) {
      console.error("Error deleting tag:", error);
      throw error;
    }
  },

  addTagToTicket: async (ticketId, tagIds) => {
    try {
      await ticketApi.addTags(ticketId, tagIds);
      await get().fetchTickets();
    } catch (error) {
      console.error("Error adding tag to ticket:", error);
      throw error;
    }
  },

  removeTagFromTicket: async (ticketId, tagId) => {
    try {
      await ticketApi.removeTag(ticketId, tagId);
      await get().fetchTickets();
    } catch (error) {
      console.error("Error removing tag from ticket:", error);
      throw error;
    }
  },

  setStatusFilter: (status) => {
    set({ statusFilter: status, page: 1 });
    get().fetchTickets();
  },

  setSelectedTagIds: (ids) => {
    set({ selectedTagIds: ids, page: 1 });
    get().fetchTickets();
  },

  setSearchQuery: (query) => {
    set({ searchQuery: query, page: 1 });
    get().fetchTickets();
  },

  setSortField: (field) => {
    set({ sortField: field, page: 1 });
    get().fetchTickets();
  },

  setSortOrder: (order) => {
    set({ sortOrder: order, page: 1 });
    get().fetchTickets();
  },

  setFilterUserId: (userId) => {
    set({ filterUserId: userId, page: 1 });
    get().fetchTickets();
  },

  setPage: (page) => {
    set({ page });
    get().fetchTickets();
  },

  setPageSize: (size) => {
    set({ pageSize: size, page: 1 });
    get().fetchTickets();
  },

  resetFilters: () => {
    set({
      statusFilter: "all",
      selectedTagIds: [],
      searchQuery: "",
      sortField: "created_at",
      sortOrder: "desc",
      filterUserId: null,
      page: 1,
      error: null,
    });
  },

  reset: () => {
    set({
      statusFilter: "all",
      selectedTagIds: [],
      searchQuery: "",
      sortField: "created_at",
      sortOrder: "desc",
      filterUserId: null,
      page: 1,
      error: null,
    });
    get().fetchTickets();
  },
}));
