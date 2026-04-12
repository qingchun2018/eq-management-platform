import type { Tag } from "./tag";

export interface TicketCreator {
  id: number;
  username: string;
}

/** 顺序工作流单步（多人接力） */
export interface WorkflowStep {
  id: number;
  step_order: number;
  name: string;
  status: "pending" | "in_progress" | "completed";
  assignee: TicketCreator;
  completed_at?: string | null;
  completion_note?: string | null;
}

export interface Ticket {
  id: number;
  project_id: number;
  title: string;
  description?: string;
  status: "pending" | "completed";
  tags: Tag[];
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  created_by?: TicketCreator | null;
  workflow_steps?: WorkflowStep[];
}

export interface WorkflowStepCreateInput {
  name: string;
  assignee_user_id: number;
}

export interface CreateTicketData {
  project_id: number;
  title: string;
  description?: string;
  tag_ids?: number[];
  workflow_steps?: WorkflowStepCreateInput[];
}

export interface UpdateTicketData {
  title?: string;
  description?: string;
  tag_ids?: number[];
}

export interface TicketListResponse {
  tickets: Ticket[];
  total: number;
  limit: number;
  offset: number;
}
