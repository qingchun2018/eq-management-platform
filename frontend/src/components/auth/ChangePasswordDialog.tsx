import { useState } from "react";
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
import { authApi } from "@/lib/api";
import { toast } from "sonner";
import { Lock } from "lucide-react";

interface ChangePasswordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const inputClass =
  "h-11 rounded-xl border-[#d2d2d7] bg-[#fafafa] px-3.5 text-[15px] text-[#1d1d1f] shadow-none transition-colors placeholder:text-[#aeaeb2] focus-visible:border-[#0071e3] focus-visible:ring-1 focus-visible:ring-[#0071e3]/35";

export default function ChangePasswordDialog({
  open,
  onOpenChange,
}: ChangePasswordDialogProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error("新密码至少 8 位");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("两次输入的新密码不一致");
      return;
    }
    setSubmitting(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast.success("密码已更新");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      onOpenChange(false);
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail
          : undefined;
      toast.error(typeof detail === "string" ? detail : "修改密码失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px] rounded-[22px] border border-[#e8e8ed] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.18)]">
        <DialogHeader className="gap-2">
          <div className="mb-1 flex h-11 w-11 items-center justify-center rounded-2xl bg-[#f5f5f7]">
            <Lock className="h-5 w-5 text-[#0071e3]" aria-hidden />
          </div>
          <DialogTitle className="text-[22px] font-semibold tracking-tight">
            修改密码
          </DialogTitle>
          <DialogDescription className="text-[15px] leading-relaxed text-[#6e6e73]">
            为保障账号安全，请先输入当前密码，再设置新密码。
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="mt-2 space-y-5">
          <div className="space-y-2">
            <Label
              htmlFor="cur-pw"
              className="text-[13px] font-medium text-[#6e6e73]"
            >
              当前密码
            </Label>
            <Input
              id="cur-pw"
              type="password"
              autoComplete="current-password"
              autoFocus
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              disabled={submitting}
              className={inputClass}
            />
          </div>
          <div className="space-y-2">
            <Label
              htmlFor="new-pw"
              className="text-[13px] font-medium text-[#6e6e73]"
            >
              新密码
            </Label>
            <Input
              id="new-pw"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={submitting}
              className={inputClass}
            />
          </div>
          <div className="space-y-2">
            <Label
              htmlFor="cf-pw"
              className="text-[13px] font-medium text-[#6e6e73]"
            >
              确认新密码
            </Label>
            <Input
              id="cf-pw"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={submitting}
              className={inputClass}
            />
          </div>

          <DialogFooter className="mt-6 gap-3 border-t border-[#f5f5f7] pt-6 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
              className="h-11 rounded-full border-[#d2d2d7] bg-white px-6 text-[15px] font-medium text-[#1d1d1f] hover:bg-[#f5f5f7]"
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="h-11 rounded-full bg-[#0071e3] px-6 text-[15px] font-medium text-white shadow-sm hover:bg-[#0077ed]"
            >
              {submitting ? "提交中..." : "保存"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
