import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { ApprovedPage } from "./pages/ApprovedPage";
import { CampaignDetailPage } from "./pages/CampaignDetailPage";
import { CampaignRadarPage } from "./pages/CampaignRadarPage";
import { DashboardPage } from "./pages/DashboardPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PublishedPage } from "./pages/PublishedPage";
import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { SettingsPage } from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/campaign-radar" element={<CampaignRadarPage />} />
        <Route path="/campaigns/:campaignId" element={<CampaignDetailPage />} />
        <Route path="/review-queue" element={<ReviewQueuePage />} />
        <Route path="/approved" element={<ApprovedPage />} />
        <Route path="/published" element={<PublishedPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
