import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { setAuthUnauthorizedHandler } from "./lib/authEvents";
import { useAuthStore } from "./store/useAuthStore";

setAuthUnauthorizedHandler(() => {
  useAuthStore.getState().logout();
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
