// 全局 401 处理：api 拦截器在刷新失败或无 refresh 时调用，触发上层 store 清状态
// 使用 setter 注入回调，避免 lib 层直接依赖 zustand store（防止循环依赖）。

type Handler = () => void;

let unauthorizedHandler: Handler | null = null;

export function setAuthUnauthorizedHandler(handler: Handler | null): void {
  unauthorizedHandler = handler;
}

export function triggerUnauthorized(): void {
  if (unauthorizedHandler) {
    try {
      unauthorizedHandler();
    } catch {
      // ignore
    }
  }
}
