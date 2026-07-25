import { AlertCircle, LoaderCircle, RefreshCw } from "lucide-react";

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Loading live data..." }: LoadingStateProps) {
  return (
    <div className="flex min-h-56 items-center justify-center rounded-2xl border border-slate-200 bg-white">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-600">
        <LoaderCircle className="h-5 w-5 animate-spin" />
        {label}
      </div>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-6 text-center">
      <AlertCircle className="mb-3 h-8 w-8 text-red-600" />
      <p className="max-w-xl text-sm font-medium text-red-800">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800"
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function NoDataState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 text-center">
      <p className="text-base font-semibold text-slate-900">{title}</p>
      <p className="mt-2 max-w-xl text-sm text-slate-500">{description}</p>
    </div>
  );
}
