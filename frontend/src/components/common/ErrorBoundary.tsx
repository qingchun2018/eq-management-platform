import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#f5f5f7] p-8">
          <div className="text-center max-w-md">
            <div className="rounded-full bg-red-50 p-4 mb-6 inline-flex">
              <AlertCircle className="h-8 w-8 text-[#ff3b30]" />
            </div>
            <h2 className="text-xl font-semibold text-[#1d1d1f] mb-2">
              页面发生错误
            </h2>
            <p className="text-[15px] text-[#86868b] mb-6">
              {this.state.error?.message || "未知错误"}
            </p>
            <Button
              onClick={this.handleReset}
              className="gap-2 bg-[#0071e3] hover:bg-[#0077ed] text-white rounded-full px-6"
            >
              <RefreshCw className="h-4 w-4" />
              重试
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
