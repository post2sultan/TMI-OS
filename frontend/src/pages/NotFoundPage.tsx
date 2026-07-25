import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/shared/PageHeader";

export function NotFoundPage() {
  return (
    <>
      <PageHeader title="Page not found" description="The requested TMI OS route does not exist." />
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-xl bg-[#10182b] px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800">
          <ArrowLeft size={16} />Return to dashboard
        </Link>
      </div>
    </>
  );
}
