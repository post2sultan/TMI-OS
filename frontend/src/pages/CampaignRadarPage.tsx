import { Radar } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";

export function CampaignRadarPage() {
  return (
    <>
      <PageHeader title="Campaign Radar" description="Discover, inspect and manage Saudi campaign intelligence from one operational workspace." />
      <EmptyState icon={Radar} title="No campaigns loaded yet" description="M2 will connect this page to the live campaign discovery and storage endpoints." note="No fake records are displayed." />
    </>
  );
}
