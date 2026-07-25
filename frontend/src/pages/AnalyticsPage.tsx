import { BarChart3 } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";

export function AnalyticsPage() {
  return (
    <>
      <PageHeader title="Analytics" description="Monitor index trends, campaign quality, throughput and publishing performance." />
      <EmptyState icon={BarChart3} title="Analytics requires live campaign history" description="Charts will be introduced only after the underlying metrics are real and verified." note="No fake records are displayed." />
    </>
  );
}
