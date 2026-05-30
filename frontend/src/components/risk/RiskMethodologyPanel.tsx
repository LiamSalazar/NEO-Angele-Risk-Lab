import { ScrollText } from "lucide-react";

type RiskMethodologyPanelProps = {
  content?: string;
};

export function RiskMethodologyPanel({ content }: RiskMethodologyPanelProps) {
  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-5">
      <div className="mb-3 flex items-center gap-2">
        <ScrollText className="h-4 w-4 text-cyan-100" />
        <h3 className="font-semibold text-white">Risk score methodology</h3>
      </div>
      <p className="text-sm leading-6 text-slate-300">
        {content?.slice(0, 700) ||
          "Risk Priority Score combines physical, orbital, close-approach, Sentry, uncertainty and data-quality components. It is experimental and intended for technical exploration only."}
      </p>
    </div>
  );
}
