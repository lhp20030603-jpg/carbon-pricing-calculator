/**
 * SPEC §8.2 Scenario JSON export/import.
 */

import type { ScenarioInputs } from "./api";

const SCHEMA_VERSION = "1.0";

export type ScenarioDocument = {
  schema_version: typeof SCHEMA_VERSION;
  meta: {
    name: string;
    created_at: string;
    notes?: string;
  };
  inputs: ScenarioInputs;
};

export function buildDocument(
  inputs: ScenarioInputs,
  meta?: Partial<ScenarioDocument["meta"]>,
): ScenarioDocument {
  return {
    schema_version: SCHEMA_VERSION,
    meta: {
      name: meta?.name ?? "Untitled scenario",
      created_at: meta?.created_at ?? new Date().toISOString(),
      notes: meta?.notes,
    },
    inputs,
  };
}

export function downloadScenarioJson(inputs: ScenarioInputs, filename?: string): void {
  const doc = buildDocument(inputs);
  const blob = new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  a.download = filename ?? `scenario_${stamp}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export type ImportResult =
  | { ok: true; inputs: ScenarioInputs }
  | { ok: false; error: string };

export async function importScenarioJson(file: File): Promise<ImportResult> {
  try {
    const text = await file.text();
    const parsed = JSON.parse(text) as Partial<ScenarioDocument>;
    if (!parsed || typeof parsed !== "object") {
      return { ok: false, error: "Not a JSON object." };
    }
    if (parsed.schema_version !== SCHEMA_VERSION) {
      return {
        ok: false,
        error: `Unsupported schema_version '${String(parsed.schema_version)}'. Expected '${SCHEMA_VERSION}'.`,
      };
    }
    if (!parsed.inputs) {
      return { ok: false, error: "Missing field: inputs" };
    }
    return { ok: true, inputs: parsed.inputs as ScenarioInputs };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `Invalid JSON: ${message}` };
  }
}
