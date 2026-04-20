/**
 * URL state (SPEC §8.3): lz-string-compressed JSON of ScenarioInputs, packed
 * into a single `?s=` query param and kept url-safe.
 */

import { compressToEncodedURIComponent, decompressFromEncodedURIComponent } from "lz-string";

import type { ScenarioInputs } from "./api";

export const URL_STATE_PARAM = "s";

export function encodeInputs(inputs: ScenarioInputs): string {
  return compressToEncodedURIComponent(JSON.stringify(inputs));
}

export function decodeInputs(raw: string): ScenarioInputs | null {
  try {
    const json = decompressFromEncodedURIComponent(raw);
    if (!json) return null;
    return JSON.parse(json) as ScenarioInputs;
  } catch {
    return null;
  }
}

export function readUrlState(): ScenarioInputs | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const raw = params.get(URL_STATE_PARAM);
  return raw ? decodeInputs(raw) : null;
}

export function writeUrlState(inputs: ScenarioInputs): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  params.set(URL_STATE_PARAM, encodeInputs(inputs));
  const next = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
  window.history.replaceState({}, "", next);
}

export async function copyShareUrl(inputs: ScenarioInputs): Promise<void> {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams();
  params.set(URL_STATE_PARAM, encodeInputs(inputs));
  const url = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
  await navigator.clipboard.writeText(url);
}
