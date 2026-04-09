import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Plus, Menu, LogOut, KeyRound, FolderPlus, Settings2 } from "lucide-react";
import SearchBar from "@/components/common/SearchBar";
import TagManager from "@/components/tags/TagManager";
import ChangePasswordDialog from "@/components/auth/ChangePasswordDialog";
import ProjectManageDialog from "@/components/project/ProjectManageDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/useAuthStore";
import { projectsApi } from "@/lib/api";
import { toast } from "sonner";

interface HeaderProps {
  onNewTicket: () => void;
  onToggleSidebar?: () => void;
  searchInputRef?: React.Ref<HTMLInputElement>;
  username?: string;
  onLogout?: () => void;
}

export default function Header({
  onNewTicket,
  onToggleSidebar,
  searchInputRef,
  username,
  onLogout,
}: HeaderProps) {
  const [pwdOpen, setPwdOpen] = useState(false);
  const [projectManageOpen, setProjectManageOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [creatingProject, setCreatingProject] = useState(false);

  const me = useAuthStore((s) => s.me);
  const projects = me?.projects ?? [];
  const currentProjectId = useAuthStore((s) => s.currentProjectId);
  const setCurrentProjectId = useAuthStore((s) => s.setCurrentProjectId);
  const refreshMe = useAuthStore((s) => s.refreshMe);
  const canWrite = useAuthStore((s) => s.canWriteInCurrentProject());
  const canManageTags = useAuthStore((s) => s.canManageTagsInCurrentProject());
  const canCreateProject = useAuthStore((s) => s.isTeamAdmin());
  const canManageMembers = useAuthStore((s) => s.canManageMembersInCurrentProject());
  const showProjectManage = canManageMembers || canCreateProject;

  const handleCreateProject = async () => {
    const name = newProjectName.trim();
    if (!name) {
      toast.error("请输入项目名称");
      return;
    }
    setCreatingProject(true);
    try {
      const p = await projectsApi.create({ name });
      setCurrentProjectId(p.id);
      await refreshMe();
      setNewProjectName("");
      setCreateProjectOpen(false);
      toast.success("项目已创建");
    } catch {
      toast.error("创建项目失败");
    } finally {
      setCreatingProject(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 backdrop-apple bg-white/80 border-b border-black/5">
      <div className="container mx-auto flex h-20 items-center justify-between px-6 md:px-8 lg:px-12 gap-4 flex-wrap">
        <div className="flex items-center gap-4 min-w-0">
          {onToggleSidebar && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleSidebar}
              className="lg:hidden h-10 w-10 transition-apple hover:bg-black/5"
            >
              <Menu className="h-5 w-5" />
            </Button>
          )}
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-[#1d1d1f] shrink-0">
            EQ 管理平台
          </h1>
          {projects.length > 0 && currentProjectId !== null && (
            <div className="hidden sm:flex items-center gap-2 min-w-[200px] max-w-[320px]">
              <Select
                value={String(currentProjectId)}
                onValueChange={(v) => setCurrentProjectId(Number(v))}
              >
                <SelectTrigger className="h-9 rounded-full border-black/10 bg-white/80">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem
                      key={p.id}
                      value={String(p.id)}
                      title={`${p.name} ${p.my_role}`}
                    >
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {showProjectManage && currentProjectId !== null && (
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 rounded-full shrink-0 border-black/10"
                  title="项目管理"
                  onClick={() => setProjectManageOpen(true)}
                >
                  <Settings2 className="h-4 w-4" />
                </Button>
              )}
              {canCreateProject && (
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 rounded-full shrink-0 border-black/10"
                  title="新建项目"
                  onClick={() => setCreateProjectOpen(true)}
                >
                  <FolderPlus className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>

        <div className="flex-1 max-w-lg mx-4 hidden md:block min-w-[120px]">
          <SearchBar inputRef={searchInputRef} />
        </div>

        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {username && (
            <span className="hidden sm:inline text-sm text-[#86868b] max-w-[120px] truncate">
              {username}
            </span>
          )}
          {onLogout && (
            <>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setPwdOpen(true)}
                className="h-10 w-10 text-[#86868b] hover:text-[#1d1d1f]"
                title="修改密码"
              >
                <KeyRound className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onLogout}
                className="h-10 w-10 text-[#86868b] hover:text-[#1d1d1f]"
                title="退出登录"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          )}
          <ChangePasswordDialog open={pwdOpen} onOpenChange={setPwdOpen} />
          <ProjectManageDialog
            open={projectManageOpen}
            onOpenChange={setProjectManageOpen}
          />
          <div className="hidden md:block">
            <TagManager disabled={!canManageTags} />
          </div>
          {canWrite && (
            <Button
              onClick={onNewTicket}
              size="default"
              className="gap-2 h-10 px-5 bg-[#0071e3] hover:bg-[#0077ed] text-white font-medium rounded-full transition-apple shadow-sm hover:shadow-md"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">新建 Ticket</span>
              <span className="sm:hidden">新建</span>
            </Button>
          )}
        </div>
      </div>

      {/* 小屏：项目选择与搜索 */}
      <div className="md:hidden px-6 pb-3 flex flex-col gap-3">
        {projects.length > 0 && currentProjectId !== null && (
          <div className="flex items-center gap-2">
            <Select
              value={String(currentProjectId)}
              onValueChange={(v) => setCurrentProjectId(Number(v))}
            >
              <SelectTrigger className="h-9 rounded-full border-black/10 flex-1">
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((p) => (
                  <SelectItem
                    key={p.id}
                    value={String(p.id)}
                    title={`${p.name} ${p.my_role}`}
                  >
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {showProjectManage && (
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9 rounded-full shrink-0"
                title="项目管理"
                onClick={() => setProjectManageOpen(true)}
              >
                <Settings2 className="h-4 w-4" />
              </Button>
            )}
            {canCreateProject && (
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9 rounded-full shrink-0"
                title="新建项目"
                onClick={() => setCreateProjectOpen(true)}
              >
                <FolderPlus className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
        <SearchBar inputRef={searchInputRef} />
      </div>

      <Dialog open={createProjectOpen} onOpenChange={setCreateProjectOpen}>
        <DialogContent className="rounded-3xl border-0 sm:max-w-md">
          <DialogHeader>
            <DialogTitle>新建项目</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label htmlFor="new-project-name">项目名称</Label>
            <Input
              id="new-project-name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="本小组内的新项目"
              className="rounded-xl"
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleCreateProject();
              }}
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setCreateProjectOpen(false)}
            >
              取消
            </Button>
            <Button
              type="button"
              className="bg-[#0071e3] hover:bg-[#0077ed]"
              disabled={creatingProject}
              onClick={() => void handleCreateProject()}
            >
              {creatingProject ? "创建中..." : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </header>
  );
}
