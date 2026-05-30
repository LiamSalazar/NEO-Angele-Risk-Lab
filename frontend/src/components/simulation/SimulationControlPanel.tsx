import { Play, WandSparkles } from "lucide-react";
import { useState } from "react";

import type { RiskObject } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { objectDisplayName, objectKey } from "@/lib/formatters";

type SimulationControlPanelProps = {
  objects?: RiskObject[];
  selectedObjectKey?: string;
  isRunning?: boolean;
  onSelectObject: (key: string) => void;
  onRun: (payload: { object_key: string; n_simulations: number; random_state?: number | null }) => void;
};

export function SimulationControlPanel({
  objects = [],
  selectedObjectKey,
  isRunning,
  onSelectObject,
  onRun
}: SimulationControlPanelProps) {
  const [nSimulations, setNSimulations] = useState(1000);
  const [manualObjectKey, setManualObjectKey] = useState(selectedObjectKey || "");
  const objectForRun = selectedObjectKey || manualObjectKey;

  return (
    <div className="console-panel rounded-lg p-5">
      <div className="mb-4 flex items-center gap-2">
        <WandSparkles className="h-5 w-5 text-cyan-100" />
        <div>
          <h2 className="font-semibold text-white">Scenario control</h2>
          <p className="text-sm text-slate-400">
            Monte Carlo perturbs score inputs; it is not orbital propagation.
          </p>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_170px_auto]">
        <div>
          <label className="technical-label mb-2 block text-[11px] text-slate-500">Object</label>
          <Input
            list="simulation-objects"
            value={objectForRun}
            onChange={(event) => {
              setManualObjectKey(event.target.value);
              onSelectObject(event.target.value);
            }}
            placeholder="object_key"
          />
          <datalist id="simulation-objects">
            {objects.slice(0, 250).map((object) => (
              <option key={objectKey(object)} value={objectKey(object)}>
                {objectDisplayName(object)}
              </option>
            ))}
          </datalist>
        </div>
        <div>
          <label className="technical-label mb-2 block text-[11px] text-slate-500">n_simulations</label>
          <Input
            type="number"
            min={1}
            max={100000}
            value={nSimulations}
            onChange={(event) => setNSimulations(Number(event.target.value))}
          />
        </div>
        <div className="flex items-end">
          <Button
            type="button"
            variant="primary"
            disabled={!objectForRun || isRunning}
            onClick={() =>
              onRun({ object_key: objectForRun, n_simulations: Math.max(1, nSimulations), random_state: 42 })
            }
            className="w-full"
          >
            <Play className="h-4 w-4" />
            {isRunning ? "Running" : "Run simulation"}
          </Button>
        </div>
      </div>
      {isRunning ? (
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-cyan-300/10">
          <div className="h-full w-1/3 rounded-full bg-cyan-300/70 animate-pulse" />
        </div>
      ) : null}
    </div>
  );
}
