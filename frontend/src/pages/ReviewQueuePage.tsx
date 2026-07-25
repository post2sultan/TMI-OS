import { ShieldCheck } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";

export function ReviewQueuePage() {
  return (
    <>
      <PageHeader title="Review Queue" description="Review the latest pending AI analysis for every campaign and take a real approval decision." />
      <EmptyState icon={ShieldCheck} title="Review queue is ready for live data" description="M3 will activate approve, reject and reanalyse actions against the existing review API." note="No fake records are displayed." />
    </>
  );
}
