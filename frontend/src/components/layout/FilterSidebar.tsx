import { useTicketStore } from "@/store/useTicketStore";
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CheckCircle2, Circle, ListTodo, X } from "lucide-react";
import { cn } from "@/lib/utils";
import TagManager from "@/components/tags/TagManager";

interface FilterSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export default function FilterSidebar({
  isOpen = true,
  onClose,
}: FilterSidebarProps) {
  const {
    tags,
    filterUsers,
    statusFilter,
    selectedTagIds,
    filterUserId,
    setStatusFilter,
    setSelectedTagIds,
    setFilterUserId,
    reset,
  } = useTicketStore();

  const toggleTagSelection = (tagId: number) => {
    if (selectedTagIds.includes(tagId)) {
      setSelectedTagIds(selectedTagIds.filter((id) => id !== tagId));
    } else {
      setSelectedTagIds([...selectedTagIds, tagId]);
    }
  };

  return (
    <aside
      className={cn(
        "w-72 border-r border-black/5 bg-white/80 backdrop-apple p-6 transition-apple-slow",
        "lg:translate-x-0 lg:static lg:z-auto",
        isOpen ? "translate-x-0" : "-translate-x-full",
        "fixed inset-y-0 left-0 z-30 lg:relative",
      )}
    >
      {onClose && (
        <div className="flex justify-end mb-6 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-10 w-10 rounded-full transition-apple hover:bg-black/5"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
      )}
      <div className="py-8">
        {/* Status Filter */}
        <div>
          <h3 className="mb-4 text-[13px] font-semibold text-[#86868b] uppercase tracking-wide">
            状态
          </h3>
          <div className="py-1.5">
            <button
              onClick={() => setStatusFilter("all")}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-4 py-3 text-[15px] font-medium transition-apple",
                statusFilter === "all"
                  ? "bg-[#0071e3] text-white shadow-sm"
                  : "text-[#1d1d1f] hover:bg-black/5",
              )}
            >
              <ListTodo className="h-4 w-4" />
              全部
            </button>
            <button
              onClick={() => setStatusFilter("pending")}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-4 py-3 text-[15px] font-medium transition-apple",
                statusFilter === "pending"
                  ? "bg-[#0071e3] text-white shadow-sm"
                  : "text-[#1d1d1f] hover:bg-black/5",
              )}
            >
              <Circle className="h-4 w-4" />
              待完成
            </button>
            <button
              onClick={() => setStatusFilter("completed")}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-4 py-3 text-[15px] font-medium transition-apple",
                statusFilter === "completed"
                  ? "bg-[#0071e3] text-white shadow-sm"
                  : "text-[#1d1d1f] hover:bg-black/5",
              )}
            >
              <CheckCircle2 className="h-4 w-4" />
              已完成
            </button>
          </div>
        </div>

        {/* 创建人 */}
        <div className="mb-8">
          <h3 className="mb-4 text-[13px] font-semibold text-[#86868b] uppercase tracking-wide">
            创建人
          </h3>
          <Select
            value={filterUserId === null ? "all" : String(filterUserId)}
            onValueChange={(v) =>
              setFilterUserId(v === "all" ? null : Number(v))
            }
          >
            <SelectTrigger className="w-full h-11 rounded-xl border-black/10 bg-white text-[15px]">
              <SelectValue placeholder="全部" />
            </SelectTrigger>
            <SelectContent className="rounded-xl border-0 shadow-apple">
              <SelectItem value="all" className="text-[15px]">
                全部
              </SelectItem>
              {filterUsers.map((u) => (
                <SelectItem
                  key={u.id}
                  value={String(u.id)}
                  className="text-[15px]"
                >
                  {u.username}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Tags Filter */}
        <div>
          <h3 className="mb-4 text-[13px] font-semibold text-[#86868b] uppercase tracking-wide">
            标签
          </h3>
          <div className="py-1.5 max-h-96 overflow-y-auto pr-2">
            {tags.map((tag) => (
              <button
                key={tag.id}
                onClick={() => toggleTagSelection(tag.id)}
                className={cn(
                  "flex w-full items-center justify-between rounded-xl px-4 py-2.5 text-[15px] transition-apple",
                  selectedTagIds.includes(tag.id)
                    ? "bg-[#0071e3]/10 text-[#0071e3]"
                    : "text-[#1d1d1f] hover:bg-black/5",
                )}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="h-3 w-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span className="font-medium">{tag.name}</span>
                </div>
                <span className="text-[13px] text-[#86868b] font-medium">
                  {tag.ticket_count || 0}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Reset Button */}
        {(statusFilter !== "all" ||
          selectedTagIds.length > 0 ||
          filterUserId !== null) && (
          <Button
            variant="outline"
            size="default"
            onClick={reset}
            className="w-full h-11 rounded-full border-black/10 text-[#1d1d1f] font-medium hover:bg-black/5 transition-apple"
          >
            清除筛选
          </Button>
        )}

        {/* Tag Manager (Mobile) */}
        <div className="md:hidden pt-4 border-t">
          <TagManager disabled={!useAuthStore.getState().canManageTagsInCurrentProject()} />
        </div>
      </div>
    </aside>
  );
}
