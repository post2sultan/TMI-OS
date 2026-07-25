import { CheckCircle2 } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";

export function ApprovedPage() {
  return (
    <>
      <PageHeader title="Approved" description="Manage analyses that have passed human review and are ready for content production." />
      <EmptyState icon={CheckCircle2} title="No approved analyses loaded" description="This page will populate directly from the backend approval state." note="No fake records are displayed." />
    </>
  );
}
