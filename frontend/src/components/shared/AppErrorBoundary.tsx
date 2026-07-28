import { Component, type ErrorInfo, type ReactNode } from "react";

interface AppErrorBoundaryProps {
  children: ReactNode;
}

interface AppErrorBoundaryState {
  failed: boolean;
}

export class AppErrorBoundary extends Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Dashboard render failed", error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
          <section className="w-full max-w-lg rounded-2xl border border-red-200 bg-white p-8 text-center shadow-sm">
            <h1 className="text-xl font-bold text-slate-950">
              The dashboard could not display this page
            </h1>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Your data is safe. Reload the dashboard to recover.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-6 rounded-xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800"
            >
              Reload dashboard
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
