import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTicketStore } from "@/store/useTicketStore";
import { useAuthStore } from "@/store/useAuthStore";
import { projectsApi } from "@/lib/api";
import { toast } from "sonner";
import TagSelector from "@/components/tags/TagSelector";
import type { Ticket } from "@/types/ticket";
import { Plus, Trash2 } from "lucide-react";

const DATA_PRESETS = ["数据爬虫", "数据清洗", "数据处理", "数据导出"];

interface TicketFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  ticket?: Ticket | null;
}

type WorkflowRow = { name: string; assignee_user_id: number | "" };

export default function TicketForm({
  open,
  onOpenChange,
  ticket,
}: TicketFormProps) {
  const { createTicket, updateTicket } = useTicketStore();
  const currentProjectId = useAuthStore((s) => s.currentProjectId);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [assignees, setAssignees] = useState<{ id: number; username: string }[]>(
    [],
  );
  const [workflowRows, setWorkflowRows] = useState<WorkflowRow[]>([]);

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    tag_ids: [] as number[],
  });

  useEffect(() => {
    if (ticket) {
      setFormData({
        title: ticket.title,
        description: ticket.description || "",
        tag_ids: ticket.tags.map((tag) => tag.id),
      });
    } else {
      setFormData({
        title: "",
        description: "",
        tag_ids: [],
      });
    }
  }, [ticket, open]);

  useEffect(() => {
    if (!open || ticket || currentProjectId === null) return;
    let cancelled = false;
    projectsApi
      .workflowAssignees(currentProjectId)
      .then((list) => {
        if (!cancelled) setAssignees(list);
      })
      .catch(() => {
        if (!cancelled) toast.error("加载可指派成员失败");
      });
    return () => {
      cancelled = true;
    };
  }, [open, ticket, currentProjectId]);

  useEffect(() => {
    if (!open && !ticket) {
      setWorkflowRows([]);
    }
  }, [open, ticket]);

  const addWorkflowRow = () => {
    setWorkflowRows((prev) => [...prev, { name: "", assignee_user_id: "" }]);
  };

  const removeWorkflowRow = (index: number) => {
    setWorkflowRows((prev) => prev.filter((_, i) => i !== index));
  };

  const updateWorkflowRow = (index: number, patch: Partial<WorkflowRow>) => {
    setWorkflowRows((prev) =>
      prev.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );
  };

  const applyDataPipelinePreset = () => {
    if (assignees.length === 0) {
      toast.error("暂无可指派成员，请确认项目成员含编辑及以上角色");
      return;
    }
    const defaultId = assignees[0].id;
    setWorkflowRows(
      DATA_PRESETS.map((name) => ({ name, assignee_user_id: defaultId })),
    );
    toast.success("已填入数据流水线四步，请为每步调整负责人");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      toast.error("请输入 Ticket 标题");
      return;
    }

    setIsSubmitting(true);

    try {
      if (ticket) {
        await updateTicket(ticket.id, {
          title: formData.title,
          description: formData.description || undefined,
          tag_ids: formData.tag_ids,
        });
        toast.success("Ticket 已更新");
      } else {
        const filled = workflowRows.filter(
          (r) => r.name.trim() && r.assignee_user_id !== "",
        );
        if (filled.length > 0) {
          const incomplete = workflowRows.some(
            (r) =>
              (r.name.trim() && r.assignee_user_id === "") ||
              (!r.name.trim() && r.assignee_user_id !== ""),
          );
          if (incomplete) {
            toast.error("工作流每一行请同时填写步骤名称与负责人，或删除空行");
            setIsSubmitting(false);
            return;
          }
        }
        await createTicket({
          ...formData,
          workflow_steps:
            filled.length > 0
              ? filled.map((r) => ({
                  name: r.name.trim(),
                  assignee_user_id: Number(r.assignee_user_id),
                }))
              : undefined,
        });
        toast.success("Ticket 已创建");
      }
      onOpenChange(false);
    } catch {
      toast.error(ticket ? "更新 Ticket 失败" : "创建 Ticket 失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto rounded-3xl border-0 shadow-xl p-0">
        <DialogHeader className="px-8 pt-8 pb-6">
          <DialogTitle className="text-2xl font-semibold text-[#1d1d1f]">
            {ticket ? "编辑 Ticket" : "创建 Ticket"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="py-6 px-8 pb-8">
          <div className="py-3">
            <Label
              htmlFor="title"
              className="text-[15px] font-medium text-[#1d1d1f]"
            >
              标题 *
            </Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="输入 Ticket 标题"
              maxLength={255}
              required
              className="h-12 rounded-xl border-black/10 bg-[#f5f5f7] text-[15px] focus:bg-white focus:shadow-apple transition-apple"
            />
          </div>

          <div className="py-3">
            <Label
              htmlFor="description"
              className="text-[15px] font-medium text-[#1d1d1f]"
            >
              描述
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="输入 Ticket 描述（可选）"
              rows={5}
              maxLength={10000}
              className="rounded-xl border-black/10 bg-[#f5f5f7] text-[15px] focus:bg-white focus:shadow-apple transition-apple resize-none"
            />
          </div>

          <div className="py-3">
            <Label className="text-[15px] font-medium text-[#1d1d1f]">
              标签
            </Label>
            <TagSelector
              selectedTagIds={formData.tag_ids}
              onChange={(tag_ids) => setFormData({ ...formData, tag_ids })}
            />
          </div>

          {!ticket && (
            <div className="py-3 border-t border-black/5 mt-2 pt-4">
              <Label className="text-[15px] font-medium text-[#1d1d1f]">
                顺序工作流（可选）
              </Label>
              <p className="text-[13px] text-[#86868b] mt-1 mb-3">
                适合数据类接力：上一步完成后自动轮到下一位负责人。留空则与普通 Ticket
                相同。
              </p>
              <div className="flex flex-wrap gap-2 mb-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="rounded-full text-[13px]"
                  onClick={applyDataPipelinePreset}
                >
                  一键填入：数据流水线四步
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="rounded-full text-[13px]"
                  onClick={addWorkflowRow}
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  添加一步
                </Button>
              </div>
              <div className="space-y-3">
                {workflowRows.map((row, index) => (
                  <div
                    key={index}
                    className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-end"
                  >
                    <div className="flex-1">
                      <Input
                        value={row.name}
                        onChange={(e) =>
                          updateWorkflowRow(index, { name: e.target.value })
                        }
                        placeholder="步骤名称，如：数据爬虫"
                        maxLength={128}
                        className="h-11 rounded-xl border-black/10 bg-[#f5f5f7] text-[15px]"
                      />
                    </div>
                    <div className="w-full sm:w-[200px]">
                      <Select
                        value={
                          row.assignee_user_id === ""
                            ? ""
                            : String(row.assignee_user_id)
                        }
                        onValueChange={(v) =>
                          updateWorkflowRow(index, {
                            assignee_user_id: v ? Number(v) : "",
                          })
                        }
                      >
                        <SelectTrigger className="h-11 rounded-xl border-black/10">
                          <SelectValue placeholder="负责人" />
                        </SelectTrigger>
                        <SelectContent>
                          {assignees.map((u) => (
                            <SelectItem key={u.id} value={String(u.id)}>
                              {u.username}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="shrink-0"
                      onClick={() => removeWorkflowRow(index)}
                      aria-label="删除该步"
                    >
                      <Trash2 className="h-4 w-4 text-[#86868b]" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="h-11 px-6 rounded-full border-black/10 text-[#1d1d1f] font-medium hover:bg-black/5 transition-apple"
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="h-11 px-6 rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-white font-medium shadow-sm hover:shadow-md transition-apple"
            >
              {isSubmitting ? "提交中..." : ticket ? "更新" : "创建"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
