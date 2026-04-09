import { useEffect, useState } from "react";
import { useTicketStore } from "@/store/useTicketStore";
import { useAuthStore } from "@/store/useAuthStore";
import TicketCard from "./TicketCard";
import BatchActions from "./BatchActions";
import SortControl from "@/components/common/SortControl";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircle, Inbox, RefreshCw } from "lucide-react";
import type { Ticket } from "@/types/ticket";

interface TicketListProps {
  onEdit: (ticket: Ticket) => void;
  onDelete: (ticket: Ticket) => void;
}

export default function TicketList({ onEdit, onDelete }: TicketListProps) {
  const {
    tickets,
    isLoading,
    error,
    toggleComplete,
    removeTagFromTicket,
    total,
    page,
    pageSize,
    setPage,
    fetchTickets,
  } = useTicketStore();

  const projects = useAuthStore((s) => s.me?.projects ?? []);
  const currentProjectId = useAuthStore((s) => s.currentProjectId);
  const canWrite = useAuthStore((s) => s.canWriteInCurrentProject());

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isBatchMode, setIsBatchMode] = useState(false);

  useEffect(() => {
    setSelectedIds([]);
    setIsBatchMode(false);
  }, [currentProjectId]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4">
        <div className="rounded-full bg-[#f5f5f7] p-6 mb-6">
          <Inbox className="h-12 w-12 text-[#86868b]" />
        </div>
        <p className="text-xl font-semibold text-[#1d1d1f] mb-2">
          暂无可访问项目
        </p>
        <p className="text-[15px] text-[#86868b] max-w-md">
          请联系组长将你加入项目，或等待组长创建新项目并分配权限。
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-40 w-full rounded-2xl bg-white/50" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4">
        <div className="rounded-full bg-red-50 p-4 mb-6">
          <AlertCircle className="h-8 w-8 text-[#ff3b30]" />
        </div>
        <p className="text-xl font-semibold text-[#1d1d1f] mb-2">加载失败</p>
        <p className="text-[15px] text-[#86868b] mb-6 max-w-md">{error}</p>
        <Button
          onClick={() => void fetchTickets()}
          className="gap-2 bg-[#0071e3] hover:bg-[#0077ed] text-white rounded-full px-6"
        >
          <RefreshCw className="h-4 w-4" />
          重试
        </Button>
      </div>
    );
  }

  const handleSelect = (ticketId: number, selected: boolean) => {
    if (selected) {
      setSelectedIds([...selectedIds, ticketId]);
    } else {
      setSelectedIds(selectedIds.filter((id) => id !== ticketId));
    }
  };

  const handleClearSelection = () => {
    setSelectedIds([]);
    setIsBatchMode(false);
  };

  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4">
        <div className="rounded-full bg-[#f5f5f7] p-6 mb-6">
          <Inbox className="h-12 w-12 text-[#86868b]" />
        </div>
        <p className="text-xl font-semibold text-[#1d1d1f] mb-2">暂无 Ticket</p>
        <p className="text-[15px] text-[#86868b] max-w-md">
          {canWrite
            ? "点击右上角「新建 Ticket」，或调整筛选条件"
            : "当前为只读权限，或列表被筛选为空。可尝试调整筛选条件。"}
        </p>
      </div>
    );
  }

  return (
    <div className="py-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          {!isBatchMode && canWrite && (
            <button
              type="button"
              onClick={() => setIsBatchMode(true)}
              className="text-[15px] text-[#0071e3] hover:text-[#0077ed] font-medium transition-apple"
            >
              批量操作
            </button>
          )}
        </div>
        <SortControl />
      </div>

      {isBatchMode && canWrite && (
        <BatchActions
          selectedIds={selectedIds}
          onClearSelection={handleClearSelection}
        />
      )}

      <div className="py-3">
        {tickets.map((ticket) => (
          <TicketCard
            key={ticket.id}
            ticket={ticket}
            onEdit={onEdit}
            onDelete={onDelete}
            onToggleComplete={(t) => toggleComplete(t.id)}
            onRemoveTag={removeTagFromTicket}
            isSelected={selectedIds.includes(ticket.id)}
            onSelect={isBatchMode ? handleSelect : undefined}
            showCheckbox={isBatchMode}
            readOnly={!canWrite}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between gap-4 pt-6 border-t border-black/5">
          <p className="text-[13px] text-[#86868b]">
            共 {total} 条，第 {page} / {totalPages} 页
          </p>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="rounded-full"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="rounded-full"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
