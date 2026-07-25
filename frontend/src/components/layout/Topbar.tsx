import { Bell, Menu, Search } from "lucide-react";
import { useLocation } from "react-router-dom";
import { navigationItems } from "../../lib/navigation";

interface TopbarProps { onMenuClick: () => void; }

export function Topbar({ onMenuClick }: TopbarProps) {
  const location = useLocation();
  const current = navigationItems.find((item) => location.pathname.startsWith(item.path)) ?? navigationItems[0];

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur-xl">
      <div className="flex h-[72px] items-center gap-4 px-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onMenuClick}
          className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm lg:hidden"
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold text-slate-900">{current.label}</p>
          <p className="truncate text-xs text-slate-500">{current.description}</p>
        </div>

        <div className="hidden w-full max-w-sm md:block">
          <div className="flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 text-slate-500">
            <Search size={16} />
            <span className="text-sm">Search TMI OS</span>
            <kbd className="ml-auto rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-semibold text-slate-400">⌘ K</kbd>
          </div>
        </div>

        <button type="button" className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50" aria-label="Notifications">
          <Bell size={18} />
        </button>

        <div className="hidden items-center gap-3 border-l border-slate-200 pl-4 sm:flex">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#10182b] text-xs font-black text-white">SS</div>
          <div className="hidden xl:block">
            <p className="text-sm font-semibold text-slate-900">Sultan Salahuddin</p>
            <p className="text-xs text-slate-500">Administrator</p>
          </div>
        </div>
      </div>
    </header>
  );
}
