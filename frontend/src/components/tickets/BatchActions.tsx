import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useTicketStore } from "@/store/useTicketStore";
import { toast } from "sonner";
import { CheckCircle2, Trash2, X } from "lucide-react";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface BatchActionsProps {
  selectedIds: number[];
  onClearSelection: () => void;
}

export default function BatchActions({
  selectedIds,
  onClearSelection,
}: BatchActionsProps) {
  const { batchComplete, batchDelete } = useTicketStore();
  const [isProcessing, setIsProcessing] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const handleBatchComplete = async () => {
    if (selectedIds.length === 0) return;

    setIsProcessing(true);
    try {
      await batchComplete(selectedIds);
      toast.success(`已标记 ${selectedIds.length} 个 Ticket 为已完成`);
      onClearSelection();
    } catch {
      toast.error("批量完成失败");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) return;

    setIsProcessing(true);
    try {
      await batchDelete(selectedIds);
      toast.success(`已删除 ${selectedIds.length} 个 Ticket`);
      onClearSelection();
      setDeleteOpen(false);
    } catch {
      toast.error("批量删除失败");
    } finally {
      setIsProcessing(false);
    }
  };

  if (selectedIds.length === 0) {
    return null;
  }

  return (
    <>
      <div className="sticky top-20 z-10 bg-white/90 backdrop-apple border-b border-black/5 p-4 rounded-2xl shadow-apple mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-[15px] font-semibold text-[#1d1d1f]">
              已选择 {selectedIds.length} 项
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              className="h-9 rounded-full text-[#0071e3] hover:text-[#0077ed] hover:bg-[#0071e3]/10 transition-apple"
            >
              <X className="h-4 w-4 mr-1" />
              取消选择
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="default"
              onClick={handleBatchComplete}
              disabled={isProcessing}
              className="gap-2 h-10 px-4 rounded-full border-black/10 text-[#1d1d1f] font-medium hover:bg-black/5 transition-apple"
            >
              <CheckCircle2 className="h-4 w-4" />
              批量完成
            </Button>
            <Button
              variant="outline"
              size="default"
              onClick={() => setDeleteOpen(true)}
              disabled={isProcessing}
              className="gap-2 h-10 px-4 rounded-full border-red-200 text-[#ff3b30] hover:text-[#ff453a] hover:bg-red-50 font-medium transition-apple"
            >
              <Trash2 className="h-4 w-4" />
              批量删除
            </Button>
          </div>
        </div>
      </div>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent className="rounded-3xl border-0">
          <AlertDialogHeader>
            <AlertDialogTitle>确认批量删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除选中的 {selectedIds.length}{" "}
              个 Ticket 吗？此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isProcessing}>取消</AlertDialogCancel>
            <Button
              type="button"
              variant="destructive"
              disabled={isProcessing}
              onClick={() => void handleBatchDelete()}
              className="bg-[#ff3b30] hover:bg-[#ff453a]"
            >
              {isProcessing ? "删除中..." : "删除"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
