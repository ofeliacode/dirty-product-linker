import type { Analysis } from "./types";

const API_ROOT = import.meta.env.VITE_API_URL ?? "";

export async function analyzeProduct(text: string): Promise<Analysis> {
  const response = await fetch(`${API_ROOT}/v1/link`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const detail = response.status === 422 ? "Enter between 1 and 500 characters." : "The inference service did not respond.";
    throw new Error(detail);
  }

  return (await response.json()) as Analysis;
}
