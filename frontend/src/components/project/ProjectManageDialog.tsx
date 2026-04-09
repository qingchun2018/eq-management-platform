import { useEffect, useState } from "react";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { auditApi, authApi, projectsApi } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import type { AuditLogItem } from "@/types/audit";
import type { ProjectMemberRow } from "@/types/project";
import { Loader2, Trash2, UserMinus } from "lucide-react";
import ConfirmDialog from "@/components/common/ConfirmDialog";

type Tab = "settings" | "members" | "audit";

interface ProjectManageDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function ProjectManageDialog({
  open,
  onOpenChange,
}: ProjectManageDialogProps) {
  const currentProjectId = useAuthStore((s) => s.currentProjectId);
  const refreshMe = useAuthStore((s) => s.refreshMe);
  const setCurrentProjectId = useAuthStore((s) => s.setCurrentProjectId);
  const me = useAuthStore((s) => s.me);
  const canManageMembers = useAuthStore((s) => s.canManageMembersInCurrentProject());
  const isTeamAdmin = useAuthStore((s) => s.isTeamAdmin());

  const [tab, setTab] = useState<Tab>("settings");
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [members, setMembers] = useState<ProjectMemberRow[]>([]);
  const [auditRows, setAuditRows] = useState<AuditLogItem[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditTeamWide, setAuditTeamWide] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);

  const [addUserId, setAddUserId] = useState<string>("");
  const [addRole, setAddRole] = useState<string>("EDITOR");
  const [teamUsers, setTeamUsers] = useState<{ id: number; username: string }[]>([]);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const currentProject = me?.projects.find((p) => p.id === currentProjectId) ?? null;

  useEffect(() => {
    if (!open || currentProjectId === null) return;

    const load = async () => {
      setLoading(true);
      try {
        const p = await projectsApi.get(currentProjectId);
        setName(p.name);
        setDescription(p.description ?? "");
        if (canManageMembers) {
          const [m, users] = await Promise.all([
            projectsApi.listMembers(currentProjectId),
            authApi.listUsers(),
          ]);
          setMembers(m);
          setTeamUsers(users);
        }
      } catch {
        toast.error("加载项目信息失败");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [open, currentProjectId, canManageMembers]);

  useEffect(() => {
    if (!open || tab !== "audit" || currentProjectId === null) return;
    const loadAudit = async () => {
      setAuditLoading(true);
      try {
        const res = await auditApi.list({
          project_id:
            isTeamAdmin && auditTeamWide ? undefined : currentProjectId,
          limit: 80,
        });
        setAuditRows(res.items);
        setAuditTotal(res.total);
      } catch {
        toast.error("加载审计日志失败");
      } finally {
        setAuditLoading(false);
      }
    };
    void loadAudit();
  }, [open, tab, currentProjectId, isTeamAdmin, auditTeamWide]);

  const handleSaveSettings = async () => {
    if (currentProjectId === null) return;
    const n = name.trim();
    if (!n) {
      toast.error("项目名称不能为空");
      return;
    }
    setLoading(true);
    try {
      await projectsApi.update(currentProjectId, {
        name: n,
        description: description.trim() || undefined,
      });
      await refreshMe();
      toast.success("已保存");
    } catch {
      toast.error("保存失败");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async () => {
    if (currentProjectId === null) return;
    setDeleting(true);
    try {
      await projectsApi.delete(currentProjectId);
      const rest = me?.projects.filter((p) => p.id !== currentProjectId) ?? [];
      if (rest.length > 0) {
        setCurrentProjectId(rest[0].id);
      }
      await refreshMe();
      toast.success("项目已删除");
      setDeleteOpen(false);
      onOpenChange(false);
    } catch {
      toast.error("删除失败");
    } finally {
      setDeleting(false);
    }
  };

  const handleAddMember = async () => {
    if (currentProjectId === null || !addUserId) return;
    setLoading(true);
    try {
      await projectsApi.addMember(currentProjectId, {
        user_id: Number(addUserId),
        role: addRole,
      });
      const m = await projectsApi.listMembers(currentProjectId);
      setMembers(m);
      setAddUserId("");
      toast.success("成员已更新");
    } catch {
      toast.error("添加失败");
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (currentProjectId === null) return;
    setLoading(true);
    try {
      await projectsApi.removeMember(currentProjectId, userId);
      setMembers((prev) => prev.filter((x) => x.user.id !== userId));
      toast.success("已移除成员");
    } catch {
      toast.error("移除失败");
    } finally {
      setLoading(false);
    }
  };

  const candidateUsers = teamUsers.filter(
    (u) => !members.some((m) => m.user.id === u.id),
  );

  if (!canManageMembers && !isTeamAdmin) {
    return null;
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg rounded-[22px] border border-[#e8e8ed]">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-[#1d1d1f]">
              项目管理
            </DialogTitle>
            <DialogDescription className="text-[15px] text-[#6e6e73]">
              {currentProject ? currentProject.name : "未选择项目"}
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-2 border-b border-[#f5f5f7] pb-2">
            {canManageMembers && (
              <>
                <button
                  type="button"
                  onClick={() => setTab("settings")}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    tab === "settings"
                      ? "bg-[#0071e3] text-white"
                      : "text-[#6e6e73] hover:bg-[#f5f5f7]"
                  }`}
                >
                  设置
                </button>
                <button
                  type="button"
                  onClick={() => setTab("members")}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    tab === "members"
                      ? "bg-[#0071e3] text-white"
                      : "text-[#6e6e73] hover:bg-[#f5f5f7]"
                  }`}
                >
                  成员
                </button>
                <button
                  type="button"
                  onClick={() => setTab("audit")}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    tab === "audit"
                      ? "bg-[#0071e3] text-white"
                      : "text-[#6e6e73] hover:bg-[#f5f5f7]"
                  }`}
                >
                  审计
                </button>
              </>
            )}
            {!canManageMembers && isTeamAdmin && (
              <button
                type="button"
                onClick={() => setTab("audit")}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  tab === "audit"
                    ? "bg-[#0071e3] text-white"
                    : "text-[#6e6e73] hover:bg-[#f5f5f7]"
                }`}
              >
                审计
              </button>
            )}
          </div>

          {currentProjectId === null ? (
            <p className="py-6 text-center text-[#86868b]">请先选择项目</p>
          ) : loading && (tab === "settings" || tab === "members") && !name ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#0071e3]" />
            </div>
          ) : (
            <>
              {tab === "settings" && canManageMembers && (
                <div className="space-y-4 pt-2">
                  <div className="space-y-2">
                    <Label htmlFor="pm-name">项目名称</Label>
                    <Input
                      id="pm-name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="rounded-xl"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pm-desc">描述</Label>
                    <Input
                      id="pm-desc"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="可选"
                      className="rounded-xl"
                    />
                  </div>
                  <DialogFooter className="gap-2 sm:justify-between">
                    <Button
                      type="button"
                      variant="outline"
                      className="text-red-600 border-red-200 hover:bg-red-50"
                      disabled={!isTeamAdmin}
                      onClick={() => setDeleteOpen(true)}
                    >
                      <Trash2 className="mr-1 h-4 w-4" />
                      删除项目
                    </Button>
                    <Button
                      type="button"
                      className="bg-[#0071e3] rounded-full"
                      onClick={() => void handleSaveSettings()}
                      disabled={loading}
                    >
                      保存
                    </Button>
                  </DialogFooter>
                  {!isTeamAdmin && (
                    <p className="text-xs text-[#86868b]">
                      仅组长可删除整个项目。
                    </p>
                  )}
                </div>
              )}

              {tab === "members" && canManageMembers && (
                <div className="space-y-4 pt-2">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
                    <div className="flex-1 space-y-2">
                      <Label>添加成员（本组用户）</Label>
                      <Select value={addUserId} onValueChange={setAddUserId}>
                        <SelectTrigger className="rounded-xl">
                          <SelectValue placeholder="选择用户" />
                        </SelectTrigger>
                        <SelectContent>
                          {candidateUsers.map((u) => (
                            <SelectItem key={u.id} value={String(u.id)}>
                              {u.username}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="w-full sm:w-36 space-y-2">
                      <Label>角色</Label>
                      <Select value={addRole} onValueChange={setAddRole}>
                        <SelectTrigger className="rounded-xl">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="PROJECT_ADMIN">管理员</SelectItem>
                          <SelectItem value="EDITOR">编辑</SelectItem>
                          <SelectItem value="VIEWER">只读</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      type="button"
                      className="rounded-full bg-[#0071e3]"
                      disabled={!addUserId || loading}
                      onClick={() => void handleAddMember()}
                    >
                      添加
                    </Button>
                  </div>

                  <ul className="divide-y divide-[#f5f5f7] rounded-xl border border-[#f5f5f7]">
                    {members.map((row) => (
                      <li
                        key={row.user.id}
                        className="flex items-center gap-2 px-3 py-2.5 text-sm"
                      >
                        <span className="min-w-0 flex-1 font-medium text-[#1d1d1f] truncate">
                          {row.user.username}
                        </span>
                        <span className="shrink-0 text-[#6e6e73]">{row.role}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 shrink-0 text-[#86868b]"
                          title="移除"
                          onClick={() => void handleRemoveMember(row.user.id)}
                          disabled={loading}
                        >
                          <UserMinus className="h-4 w-4" />
                        </Button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {tab === "audit" && (canManageMembers || isTeamAdmin) && (
                <div className="space-y-3 pt-2">
                  {isTeamAdmin && (
                    <label className="flex items-center gap-2 text-sm text-[#6e6e73]">
                      <input
                        type="checkbox"
                        checked={auditTeamWide}
                        onChange={(e) => setAuditTeamWide(e.target.checked)}
                        className="rounded border-[#d2d2d7]"
                      />
                      查看本组全部项目与账号操作
                    </label>
                  )}
                  {auditLoading && auditRows.length === 0 ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-7 w-7 animate-spin text-[#0071e3]" />
                    </div>
                  ) : (
                    <div className="max-h-[50vh] overflow-auto rounded-xl border border-[#f5f5f7] text-xs">
                      <table className="w-full border-collapse">
                        <thead className="sticky top-0 bg-[#fafafa] text-left text-[#6e6e73]">
                          <tr>
                            <th className="p-2 font-medium">时间</th>
                            <th className="p-2 font-medium">用户</th>
                            <th className="p-2 font-medium">操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {auditRows.map((row) => (
                            <tr key={row.id} className="border-t border-[#f5f5f7]">
                              <td className="p-2 whitespace-nowrap text-[#86868b]">
                                {format(
                                  new Date(row.created_at),
                                  "MM-dd HH:mm:ss",
                                )}
                              </td>
                              <td className="p-2">{row.username ?? "-"}</td>
                              <td className="p-2 break-all">
                                {row.action}
                                {row.detail ? (
                                  <span className="text-[#86868b]">
                                    {" "}
                                    {row.detail}
                                  </span>
                                ) : null}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {auditRows.length === 0 && (
                        <p className="p-4 text-center text-[#86868b]">暂无记录</p>
                      )}
                      <p className="border-t border-[#f5f5f7] p-2 text-[#86868b]">
                        共 {auditTotal} 条
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="删除项目"
        description="将永久删除该项目及其下所有 Ticket、标签，且不可恢复。确定继续？"
        confirmText={deleting ? "删除中..." : "确定删除"}
        onConfirm={() => void handleDeleteProject()}
      />
    </>
  );
}
