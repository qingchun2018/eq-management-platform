import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import axios from "axios";
import { useAuthStore } from "@/store/useAuthStore";
import { toast } from "sonner";

function formatAuthError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.code === "ECONNABORTED") {
      return "请求超时：请确认本机已启动后端（默认 uvicorn 8000）且 PostgreSQL 可连接";
    }
    if (!err.response) {
      return "无法连接后端：请在 backend 目录启动 API（端口 8000），并检查数据库是否运行";
    }
    const raw = err.response.data as { detail?: unknown } | undefined;
    const d = raw?.detail;
    if (typeof d === "string") return d;
  }
  return "操作失败，请检查网络或账号信息";
}

export default function LoginPage() {
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      toast.error("请填写用户名和密码");
      return;
    }
    if (mode === "register" && password.length < 8) {
      toast.error("密码至少 8 位，与服务器要求一致");
      return;
    }
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password);
      }
      toast.success(mode === "login" ? "登录成功" : "注册并登录成功");
    } catch (err: unknown) {
      const ax = err as {
        response?: { status?: number; data?: { detail?: string } };
      };
      if (ax.response?.status === 429) {
        return;
      }
      toast.error(formatAuthError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f5f5f7] p-6">
      <Card className="w-full max-w-md border-black/5 shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-semibold text-[#1d1d1f]">
            EQ 管理平台
          </CardTitle>
          <CardDescription>
            {mode === "login" ? "登录以管理 Ticket" : "注册新账号（需后端开启注册）"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={submitting}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={submitting}
              />
              {mode === "register" && (
                <p className="text-xs text-[#86868b]">
                  至少 8 位字符，请勿使用过于简单的密码。
                </p>
              )}
            </div>
            <Button
              type="submit"
              className="w-full bg-[#0071e3] hover:bg-[#0077ed] text-white"
              disabled={submitting}
            >
              {submitting ? "请稍候..." : mode === "login" ? "登录" : "注册并登录"}
            </Button>
            <button
              type="button"
              className="w-full text-sm text-[#0071e3] hover:underline"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              disabled={submitting}
            >
              {mode === "login" ? "没有账号？注册" : "已有账号？去登录"}
            </button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
