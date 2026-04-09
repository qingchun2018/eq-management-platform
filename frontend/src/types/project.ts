/** 与后端 /auth/me、/projects 对齐 */

export type ProjectRole = "PROJECT_ADMIN" | "EDITOR" | "VIEWER";

export interface TeamBrief {
  id: number;
  name: string;
  slug: string;
}

export interface ProjectBrief {
  id: number;
  team_id: number;
  name: string;
  description?: string | null;
  my_role: ProjectRole;
}

export interface MeResponse {
  id: number;
  username: string;
  team: TeamBrief | null;
  team_role: string | null;
  projects: ProjectBrief[];
}

/** 与 GET /projects/{id}/members 单项对齐 */
export interface ProjectMemberRow {
  user: { id: number; username: string };
  role: string;
}

/** 当前项目内是否可改 Ticket（创建/编辑/完成/删） */
export function roleCanWriteTicket(role: string | null | undefined): boolean {
  return role === "PROJECT_ADMIN" || role === "EDITOR";
}

/** 是否可管理标签 */
export function roleCanManageTags(role: string | null | undefined): boolean {
  return role === "PROJECT_ADMIN" || role === "EDITOR";
}

/** 是否可管理项目成员 */
export function roleCanManageMembers(role: string | null | undefined): boolean {
  return role === "PROJECT_ADMIN";
}
