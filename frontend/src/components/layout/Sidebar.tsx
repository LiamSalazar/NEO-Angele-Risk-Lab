import { NavLink } from "react-router-dom";

import { APP_NAME, NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-cyan-300/12 bg-[#040914]/86 backdrop-blur-xl lg:block">
      <div className="flex h-full flex-col">
        <div className="border-b border-cyan-300/12 p-5">
          <p className="technical-label text-[11px] text-cyan-100">Mission observatory</p>
          <h1 className="mt-2 text-xl font-semibold text-white">{APP_NAME}</h1>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center gap-3 rounded-md border px-3 py-2.5 text-sm transition",
                    isActive
                      ? "border-cyan-300/30 bg-cyan-300/12 text-cyan-50"
                      : "border-transparent text-slate-400 hover:border-cyan-300/15 hover:bg-white/5 hover:text-slate-100"
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        <div className="border-t border-cyan-300/12 p-4">
          <p className="font-mono text-xs leading-5 text-slate-500">
            Experimental NEO risk intelligence. Not an official alerting system.
          </p>
        </div>
      </div>
    </aside>
  );
}
