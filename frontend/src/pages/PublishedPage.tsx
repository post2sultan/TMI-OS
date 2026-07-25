import { NoDataState } from "../components/shared/LiveState";

export function PublishedPage() {
  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">DISTRIBUTION</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Published
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Publishing records will appear here once the backend publishing module is available.
        </p>
      </header>
      <NoDataState
        title="Publishing API not available"
        description="The current live OpenAPI contract contains no publishing endpoint, so this screen does not fabricate records."
      />
    </div>
  );
}
