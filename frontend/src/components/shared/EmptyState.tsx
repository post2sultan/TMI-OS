import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  note?: string;
}

export function EmptyState({ icon: Icon, title, description, note }: EmptyStateProps) {
  return (
    <section className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center shadow-sm shadow-slate-200/30">
      <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-slate-100 text-slate-500">
        <Icon size={24} />
      </div>
      <h2 className="mt-5 text-lg font-bold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">{description}</p>
      {note ? <p className="mx-auto mt-4 max-w-xl rounded-lg bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">{note}</p> : null}
    </section>
  );
}
