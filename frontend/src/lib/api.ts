/**
 * Thin fetch wrapper around the FastAPI backend. Types are the ones generated
 * by `openapi-typescript` — single source of truth (SPEC §6.3).
 */

import type { components } from "../types/api";

export type Caveat = components["schemas"]["Caveat"];
export type CoefficientRecord = components["schemas"]["CoefficientRecord"];
export type ComputeRequest = components["schemas"]["ComputeRequest"];
export type ComputeResponse = components["schemas"]["ComputeResponse"];
export type HealthResponse = components["schemas"]["HealthResponse"];
export type KPIBundle = components["schemas"]["KPIBundle"];
export type PercentileBands = components["schemas"]["PercentileBands"];
export type PricePoint = components["schemas"]["PricePoint"];
export type ReferenceEntry = components["schemas"]["ReferenceEntry"];
export type ScenarioInputs = components["schemas"]["ScenarioInputs"];
export type ScenarioPreset = components["schemas"]["ScenarioPreset"];

const DEFAULT_BASE = "/api";
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await parseBody(res);
  if (!res.ok) {
    const message =
      body && typeof body === "object" && "detail" in (body as Record<string, unknown>)
        ? String((body as Record<string, unknown>).detail)
        : res.statusText;
    throw new ApiError(res.status, message, body);
  }
  return body as T;
}

export const api = {
  health: (): Promise<HealthResponse> => request("/health"),
  scenarios: (): Promise<ScenarioPreset[]> => request("/scenarios"),
  references: (): Promise<ReferenceEntry[]> => request("/references"),
  compute: (inputs: ScenarioInputs): Promise<ComputeResponse> =>
    request("/compute", { method: "POST", body: JSON.stringify({ inputs }) }),
};
