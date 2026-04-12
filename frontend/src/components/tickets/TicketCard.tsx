import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Edit, Trash2, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import type { Ticket, WorkflowStep } from "@/types/ticket";
import TagBadge from "@/components/tags/TagBadge";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/useAuthStore";
import { useTicketStore } from "@/store/useTicketStore";

interface TicketCardProps {
  ticket: Ticket;
  onEdit: (ticket: Ticket) => void;
  onDelete: (ticket: Ticket) => void;
  onToggleComplete: (ticket: Ticket) => void;
  onRemoveTag?: (ticketId: number, tagId: number) => void;
  isSelected?: boolean;
  onSelect?: (ticketId: number, selected: boolean) => void;
  showCheckbox?: boolean;
  /** 只读：仅查看，不可改状态、标签、编辑删除 */
  readOnly?: boolean;
}

function stepStatusLabel(s: WorkflowStep) {
  if (s.status === "completed") return "已完成";
  if (s.status === "in_progress") return "进行中";
  return "待开始";
}

export default function TicketCard({
  ticket,
  onEdit,
  onDelete,
  onToggleComplete,
  onRemoveTag,
  isSelected = false,
  onSelect,
  showCheckbox = false,
  readOnly = false,
}: TicketCardProps) {
  const isCompleted = ticket.status === "completed";
  const me = useAuthStore((s) => s.me);
  const canManageMembers = useAuthStore((s) => s.canManageMembersInCurrentProject());
  const { completeWorkflowStep } = useTicketStore();

  const workflowSteps = ticket.workflow_steps ?? [];
  const hasWorkflow = workflowSteps.length > 0;
  const currentStep = workflowSteps.find((s) => s.status === "in_progress");

  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [pendingStep, setPendingStep] = useState<WorkflowStep | null>(null);
  const [stepNote, setStepNote] = useState("");
  const [stepSubmitting, setStepSubmitting] = useState(false);

  const canActCurrentStep =
    currentStep &&
    me &&
    (currentStep.assignee.id === me.id || canManageMembers);

  const openCompleteStep = (step: WorkflowStep) => {
    setPendingStep(step);
    setStepNote("");
    setNoteDialogOpen(true);
  };

  const submitCompleteStep = async () => {
    if (!pendingStep) return;
    setStepSubmitting(true);
    try {
      await completeWorkflowStep(
        ticket.id,
        pendingStep.id,
        stepNote.trim() || undefined,
      );
      setNoteDialogOpen(false);
      setPendingStep(null);
    } finally {
      setStepSubmitting(false);
    }
  };

  const checkboxDisabled = readOnly || hasWorkflow;

  return (
    <>
      <Card
        className={cn(
          "p-6 transition-apple border-0 shadow-apple hover:shadow-apple-hover bg-white rounded-2xl",
          isCompleted && "opacity-75",
          isSelected && "ring-2 ring-[#0071e3] ring-offset-2",
        )}
      >
        <div className="flex items-start gap-4">
          {showCheckbox && onSelect ? (
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) =>
                onSelect(ticket.id, checked as boolean)
              }
              className="mt-0.5 h-5 w-5"
            />
          ) : (
            <Checkbox
              checked={isCompleted}
              disabled={checkboxDisabled}
              onCheckedChange={() => {
                if (!readOnly && !checkboxDisabled) onToggleComplete(ticket);
              }}
              className="mt-0.5 h-5 w-5 transition-apple"
            />
          )}

          <div className="flex-1 py-3 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <h3
                className={cn(
                  "text-xl font-semibold text-[#1d1d1f] leading-tight",
                  isCompleted && "line-through text-[#86868b]",
                )}
              >
                {ticket.title}
              </h3>

              {!readOnly && (
                <div className="flex gap-1 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(ticket)}
                    className="h-9 w-9 rounded-full transition-apple hover:bg-black/5 text-[#1d1d1f]"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(ticket)}
                    className="h-9 w-9 rounded-full transition-apple hover:bg-red-50 text-[#ff3b30] hover:text-[#ff453a]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            {ticket.description && (
              <p className="text-[15px] text-[#86868b] leading-relaxed line-clamp-2">
                {ticket.description}
              </p>
            )}

            {hasWorkflow && (
              <div className="mt-3 rounded-xl bg-[#f5f5f7] p-4 space-y-2">
                <p className="text-[13px] font-medium text-[#6e6e73]">
                  顺序工作流
                </p>
                <div className="space-y-2">
                  {workflowSteps.map((s, idx) => (
                    <div
                      key={s.id}
                      className={cn(
                        "flex flex-wrap items-center gap-2 text-[14px]",
                        s.status === "in_progress" &&
                          "text-[#0071e3] font-medium",
                        s.status === "completed" && "text-[#86868b]",
                      )}
                    >
                      <span className="tabular-nums text-[#86868b] w-5">
                        {idx + 1}.
                      </span>
                      <span>{s.name}</span>
                      <ChevronRight className="h-3.5 w-3.5 text-[#c7c7cc] shrink-0" />
                      <span>{s.assignee.username}</span>
                      <span className="text-[12px] rounded-full px-2 py-0.5 bg-white/80">
                        {stepStatusLabel(s)}
                      </span>
                    </div>
                  ))}
                </div>
                {currentStep && canActCurrentStep && !readOnly && (
                  <Button
                    type="button"
                    size="sm"
                    className="mt-2 rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-white"
                    onClick={() => openCompleteStep(currentStep)}
                  >
                    完成本步（{currentStep.name}）
                  </Button>
                )}
                {currentStep && !canActCurrentStep && !readOnly && (
                  <p className="text-[13px] text-[#86868b] mt-1">
                    当前由 {currentStep.assignee.username} 处理本步
                  </p>
                )}
              </div>
            )}

            {ticket.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {ticket.tags.map((tag) => (
                  <TagBadge
                    key={tag.id}
                    tag={tag}
                    removable={!readOnly && !isCompleted}
                    onRemove={
                      onRemoveTag && !readOnly
                        ? () => onRemoveTag(ticket.id, tag.id)
                        : undefined
                    }
                  />
                ))}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-[13px] text-[#86868b] pt-2">
              {ticket.created_by && (
                <span>创建人 {ticket.created_by.username}</span>
              )}
              <span>
                创建于 {format(new Date(ticket.created_at), "yyyy-MM-dd HH:mm")}
              </span>
              {ticket.completed_at && (
                <span>
                  完成于{" "}
                  {format(new Date(ticket.completed_at), "yyyy-MM-dd HH:mm")}
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      <Dialog open={noteDialogOpen} onOpenChange={setNoteDialogOpen}>
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle>完成步骤</DialogTitle>
          </DialogHeader>
          <p className="text-[14px] text-[#86868b]">
            {pendingStep ? `确认完成「${pendingStep.name}」？可选填备注。` : ""}
          </p>
          <Textarea
            value={stepNote}
            onChange={(e) => setStepNote(e.target.value)}
            placeholder="完成说明（可选）"
            rows={3}
            maxLength={10000}
            className="rounded-xl"
          />
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              className="rounded-full"
              onClick={() => setNoteDialogOpen(false)}
            >
              取消
            </Button>
            <Button
              className="rounded-full bg-[#0071e3]"
              disabled={stepSubmitting}
              onClick={() => void submitCompleteStep()}
            >
              {stepSubmitting ? "提交中..." : "确认完成"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
