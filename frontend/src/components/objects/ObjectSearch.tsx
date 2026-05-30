import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import type { RiskObject } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { objectDisplayName, objectKey } from "@/lib/formatters";

type ObjectSearchProps = {
  objects?: RiskObject[];
  onSelect: (objectKey: string) => void;
  placeholder?: string;
};

export function ObjectSearch({ objects = [], onSelect, placeholder = "Search object_key, designation or name" }: ObjectSearchProps) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return objects.slice(0, 8);
    }
    return objects
      .filter((object) =>
        [objectKey(object), objectDisplayName(object), object.des, object.name, object.full_name]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(normalized))
      )
      .slice(0, 8);
  }, [objects, query]);

  const submit = () => {
    const selected = matches[0];
    const key = selected ? objectKey(selected) : query.trim();
    if (key) {
      onSelect(key);
    }
  };

  return (
    <div className="rounded-lg border border-cyan-300/14 bg-slate-950/45 p-4">
      <label className="technical-label mb-2 block text-[11px] text-slate-500">Object lookup</label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                submit();
              }
            }}
            placeholder={placeholder}
            className="pl-9"
          />
        </div>
        <Button type="button" onClick={submit} variant="primary">
          Acquire
        </Button>
      </div>
      {matches.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {matches.map((object) => {
            const key = objectKey(object);
            return (
              <button
                key={key}
                type="button"
                className="rounded-full border border-cyan-300/15 bg-cyan-300/8 px-3 py-1 text-xs text-cyan-100 transition hover:border-cyan-300/35"
                onClick={() => onSelect(key)}
              >
                {objectDisplayName(object)}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
