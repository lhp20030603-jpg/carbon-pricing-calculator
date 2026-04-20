import { useRef, useState } from "react";

import type { ScenarioInputs } from "../lib/api";
import { downloadScenarioJson, importScenarioJson } from "../lib/json-export";
import { copyShareUrl } from "../lib/url-state";
import { Button } from "./primitives";

export function ActionButtons({
  inputs,
  onCompute,
  onImport,
  computing,
}: {
  inputs: ScenarioInputs;
  onCompute: () => void;
  onImport: (inputs: ScenarioInputs) => void;
  computing: boolean;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [toast, setToast] = useState<string | null>(null);

  const handleShare = async () => {
    try {
      await copyShareUrl(inputs);
      setToast("Share link copied");
    } catch {
      setToast("Clipboard unavailable");
    }
    setTimeout(() => setToast(null), 2200);
  };

  const handleImportFile = async (file: File) => {
    const res = await importScenarioJson(file);
    if ("inputs" in res) {
      onImport(res.inputs);
      setToast("Scenario imported");
    } else {
      setToast(`Import failed: ${res.error}`);
    }
    setTimeout(() => setToast(null), 3200);
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <Button onClick={onCompute} disabled={computing} className="flex-1">
          {computing ? "Computing…" : "Compute"}
        </Button>
        <Button variant="secondary" onClick={() => downloadScenarioJson(inputs)}>
          Export
        </Button>
        <Button
          variant="secondary"
          onClick={() => fileInput.current?.click()}
          title="Import a scenario JSON file"
        >
          Import
        </Button>
        <Button variant="secondary" onClick={handleShare} title="Copy share URL">
          Share URL
        </Button>
      </div>
      <input
        ref={fileInput}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleImportFile(file);
          e.target.value = "";
        }}
      />
      {toast ? (
        <div
          role="status"
          className="rounded-md border border-[color:var(--color-ink-100)] bg-[color:var(--color-ink-50)] px-2 py-1 text-xs text-[color:var(--color-ink-700)]"
        >
          {toast}
        </div>
      ) : null}
    </div>
  );
}
