import {
  BarChart3,
  CheckCircle2,
  LayoutDashboard,
  Radar,
  Send,
  Settings,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export interface NavigationItem {
  label: string;
  path: string;
  icon: LucideIcon;
  description: string;
}

export const navigationItems: NavigationItem[] = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard, description: "Executive command centre" },
  { label: "Campaign Radar", path: "/campaign-radar", icon: Radar, description: "Discover and manage campaigns" },
  { label: "Review Queue", path: "/review-queue", icon: ShieldCheck, description: "Review AI analysis" },
  { label: "Approved", path: "/approved", icon: CheckCircle2, description: "Approved campaign analyses" },
  { label: "Published", path: "/published", icon: Send, description: "Published TMI content" },
  { label: "Analytics", path: "/analytics", icon: BarChart3, description: "Performance and index trends" },
  { label: "Settings", path: "/settings", icon: Settings, description: "System configuration" },
];
