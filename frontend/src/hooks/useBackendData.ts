/**
 * react-query wrappers for the three read-only backend endpoints.
 * `useHealthPing` exists to pre-warm the Render Free cold start on page mount.
 */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { ScenarioInputs } from "../lib/api";

export function useHealthPing() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    staleTime: 60_000,
    retry: 2,
  });
}

export function useScenarioPresets() {
  return useQuery({
    queryKey: ["scenarios"],
    queryFn: api.scenarios,
    staleTime: Infinity,
  });
}

export function useReferences() {
  return useQuery({
    queryKey: ["references"],
    queryFn: api.references,
    staleTime: Infinity,
  });
}

export function useComputeMutation() {
  return useMutation({
    mutationFn: (inputs: ScenarioInputs) => api.compute(inputs),
  });
}
