import { Activity, CheckCircle2, Radar, ShieldCheck, Sparkles } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";
import { StatusCard } from "../components/shared/StatusCard";

export function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="Executive command centre"
        title="Dashboard"
        description="A single view of campaign discovery, AI analysis, human review and publishing performance."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard title="Campaigns discovered" value="—" caption="Live value will be connected in M2." icon={Radar} />
        <StatusCard title="Awaiting review" value="—" caption="Latest pending analysis only." icon={ShieldCheck} />
        <StatusCard title="Approved" value="—" caption="Approved analyses ready for publishing." icon={CheckCircle2} />
        <StatusCard title="System health" value="Shell" caption="Frontend navigation and routing are active." icon={Activity} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <EmptyState
          icon={Sparkles}
          title="Live dashboard data is the next connection"
          description="The visual system is ready. M2 will connect this dashboard to the existing FastAPI endpoints without introducing fake metrics."
          note="Function first: figures remain intentionally blank until the backend is connected."
        />

        <section className="rounded-2xl border border-slate-200 bg-[#10182b] p-6 text-white shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-300">M1 status</p>
          <h2 className="mt-3 text-xl font-black">Application shell operational</h2>
          <div className="mt-5 space-y-3 text-sm text-slate-300">
            {["Responsive navigation", "Seven working routes", "Executive visual framework", "Backend-ready page structure"].map((item) => (
              <div key={item} className="flex items-center gap-3">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
