import type { LucideIcon } from "lucide-react";

interface StatusCardProps {
  title: string;
  value: string;
  caption: string;
  icon: LucideIcon;
}

export function StatusCard({ title, value, caption, icon: Icon }: StatusCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-black tracking-tight text-slate-950">{value}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500">{caption}</p>
        </div>
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-700">
          <Icon size={20} />
        </div>
      </div>
    </article>
  );
}
