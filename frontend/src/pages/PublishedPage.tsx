import { Send } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";

export function PublishedPage() {
  return (
    <>
      <PageHeader title="Published" description="Track campaign analyses and TMI content that have completed the publishing workflow." />
      <EmptyState icon={Send} title="No published content loaded" description="Publishing records will appear here once the real workflow is connected." note="No fake records are displayed." />
    </>
  );
}
