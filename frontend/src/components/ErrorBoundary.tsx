import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  fallback: (args: { error: Error; reset: () => void }) => ReactNode;
  children: ReactNode;
};

type State = { error: Error | null };

/**
 * Class-based error boundary.
 *
 * React 18 still requires a class component for boundaries (no hook API). We
 * use this to contain render crashes from the Plotly chart so a single broken
 * trace doesn't take the whole app down.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error) {
      return this.props.fallback({ error: this.state.error, reset: this.handleReset });
    }
    return this.props.children;
  }
}
