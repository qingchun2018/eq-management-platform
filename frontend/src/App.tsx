import { useState, useEffect, useRef, useCallback } from "react";
import { useTicketStore } from "./store/useTicketStore";
import { useAuthStore } from "./store/useAuthStore";
import Header from "./components/layout/Header";
import FilterSidebar from "./components/layout/FilterSidebar";
import TicketList from "./components/tickets/TicketList";
import TicketForm from "./components/tickets/TicketForm";
import ConfirmDialog from "./components/common/ConfirmDialog";
import LoginPage from "./components/auth/LoginPage";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import type { Ticket } from "./types/ticket";

function TicketApp() {
  const { fetchTags, fetchFilterUsers, deleteTicket, fetchTickets, resetFilters } =
    useTicketStore();
  const logout = useAuthStore((s) => s.logout);
  const username = useAuthStore((s) => s.username);
  const currentProjectId = useAuthStore((s) => s.currentProjectId);
  const canWrite = useAuthStore((s) => s.canWriteInCurrentProject());
  const searchInputRef = useRef<HTMLInputElement>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);
  const [deletingTicket, setDeletingTicket] = useState<Ticket | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleNewTicket = useCallback(() => {
    setEditingTicket(null);
    setIsFormOpen(true);
  }, []);

  useEffect(() => {
    resetFilters();
    void fetchTags();
    void fetchFilterUsers();
    void fetchTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentProjectId]);

  // 键盘快捷键支持
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K: Focus search
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }

      // N: New ticket（仅在有编辑权限且非输入框时）
      if (
        e.key === "n" &&
        !e.ctrlKey &&
        !e.metaKey &&
        canWrite
      ) {
        const target = e.target as HTMLElement;
        if (
          target.tagName !== "INPUT" &&
          target.tagName !== "TEXTAREA" &&
          !target.isContentEditable
        ) {
          handleNewTicket();
        }
      }

      // Escape: Close modals/sidebar
      if (e.key === "Escape") {
        if (isFormOpen) {
          setIsFormOpen(false);
        }
        if (isSidebarOpen) {
          setIsSidebarOpen(false);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFormOpen, isSidebarOpen, handleNewTicket, canWrite]);

  const handleEditTicket = (ticket: Ticket) => {
    setEditingTicket(ticket);
    setIsFormOpen(true);
  };

  const handleDeleteTicket = (ticket: Ticket) => {
    setDeletingTicket(ticket);
  };

  const confirmDelete = async () => {
    if (!deletingTicket) return;

    try {
      await deleteTicket(deletingTicket.id);
      toast.success("Ticket 已删除");
      setDeletingTicket(null);
    } catch {
      toast.error("删除 Ticket 失败");
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <Header
        username={username ?? undefined}
        onLogout={logout}
        onNewTicket={handleNewTicket}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        searchInputRef={searchInputRef}
      />

      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-apple z-20 lg:hidden transition-apple"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <div className="flex">
        <FilterSidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />
        <main className="flex-1 p-6 md:p-8 lg:p-12 lg:ml-0 w-full">
          <TicketList onEdit={handleEditTicket} onDelete={handleDeleteTicket} />
        </main>
      </div>

      <TicketForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        ticket={editingTicket}
      />

      <ConfirmDialog
        open={!!deletingTicket}
        onOpenChange={(open) => !open && setDeletingTicket(null)}
        title="删除 Ticket"
        description={`确定要删除 "${deletingTicket?.title}" 吗？此操作无法撤销。`}
        onConfirm={confirmDelete}
        confirmText="删除"
        cancelText="取消"
      />
    </div>
  );
}

export default function App() {
  const { isReady, username, bootstrap } = useAuthStore();

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  return (
    <>
      {!isReady ? (
        <div className="min-h-screen flex items-center justify-center bg-[#f5f5f7]">
          <p className="text-[#86868b]">加载中...</p>
        </div>
      ) : !username ? (
        <LoginPage />
      ) : (
        <TicketApp />
      )}
      <Toaster />
    </>
  );
}
