import type { Tag } from "./tag";

export interface TicketCreator {
  id: number;
  username: string;
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
}

export interface CreateTicketData {
  project_id: number;
  title: string;
  description?: string;
  tag_ids?: number[];
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
