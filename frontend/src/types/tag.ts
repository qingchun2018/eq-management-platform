export interface Tag {
  id: number;
  name: string;
  color: string;
  created_at: string;
  ticket_count?: number;
}

export interface CreateTagData {
  project_id: number;
  name: string;
  color?: string;
}

/** PATCH /tags/:id 至少填一项 */
export interface TagUpdateData {
  name?: string;
  color?: string;
}

export interface TagListResponse {
  tags: Tag[];
  total: number;
}
