import { Settings } from "lucide-react";
import { EmptyState } from "../components/shared/EmptyState";
import { PageHeader } from "../components/shared/PageHeader";

export function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" description="Configure system behaviour, AI providers, discovery sources and publishing controls." />
      <EmptyState icon={Settings} title="Configuration interface prepared" description="Later milestones will expose only settings backed by working services." note="No decorative controls are presented as functional." />
    </>
  );
}
