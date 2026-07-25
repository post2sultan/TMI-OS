import { X } from "lucide-react";
import { NavLink } from "react-router-dom";
import { navigationItems } from "../../lib/navigation";

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col bg-[#10182b] text-white">
      <div className="border-b border-white/10 px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-white text-sm font-black tracking-tight text-[#10182b] shadow-lg shadow-black/20">
            TMI
          </div>
          <div>
            <p className="text-base font-bold tracking-tight">TMI OS</p>
            <p className="mt-0.5 text-xs text-slate-400">Campaign Intelligence</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  "group flex items-center gap-3 rounded-xl px-3 py-3 transition",
                  isActive
                    ? "bg-white text-[#10182b] shadow-lg shadow-black/20"
                    : "text-slate-300 hover:bg-white/10 hover:text-white",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <span className={[
                    "grid h-9 w-9 place-items-center rounded-lg transition",
                    isActive ? "bg-[#10182b] text-white" : "bg-white/5 text-slate-300 group-hover:bg-white/10",
                  ].join(" ")}>
                    <Icon size={18} strokeWidth={2} />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold">{item.label}</span>
                    <span className="mt-0.5 block truncate text-[11px] text-slate-500">{item.description}</span>
                  </span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Environment</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />Local
            </span>
          </div>
          <p className="mt-2 text-[11px] leading-5 text-slate-500">M1 application shell</p>
        </div>
      </div>
    </div>
  );
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 lg:block">
        <SidebarContent />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
            onClick={onMobileClose}
            aria-label="Close navigation"
          />
          <aside className="relative h-full w-[88%] max-w-80 shadow-2xl">
            <button
              type="button"
              onClick={onMobileClose}
              className="absolute right-4 top-5 z-10 grid h-9 w-9 place-items-center rounded-lg bg-white/10 text-white hover:bg-white/20"
              aria-label="Close navigation"
            >
              <X size={18} />
            </button>
            <SidebarContent onNavigate={onMobileClose} />
          </aside>
        </div>
      ) : null}
    </>
  );
}
