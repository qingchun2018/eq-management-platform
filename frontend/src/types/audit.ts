/** 与 GET /audit-logs 对齐 */

export interface AuditLogItem {
  id: number;
  username: string | null;
  action: string;
  resource_type: string;
  resource_id: number | null;
  project_id: number | null;
  detail: string | null;
  request_id: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  skip: number;
  limit: number;
}
