import type { Analysis, Extraction } from "./types";

const API_ROOT = import.meta.env.VITE_API_URL ?? "";

const RETRYABLE_STATUS = new Set([404, 502, 503, 504]);

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function requestAnalysis(text: string, endpoint: string): Promise<Response> {
  return fetch(`${API_ROOT}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
}

async function requestResult<T>(text: string, endpoint: string): Promise<T> {
  let response: Response;
  try {
    response = await requestAnalysis(text, endpoint);
    if (RETRYABLE_STATUS.has(response.status)) {
      await delay(1200);
      response = await requestAnalysis(text, endpoint);
    }
  } catch {
    await delay(1200);
    try {
      response = await requestAnalysis(text, endpoint);
    } catch {
      throw new Error("The free inference service is waking up. Wait a moment and try again.");
    }
  }

  if (!response.ok) {
    const detail = response.status === 422
      ? "Enter between 1 and 500 characters."
      : "The inference service is temporarily unavailable. Try again shortly.";
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export function analyzeProduct(text: string): Promise<Analysis> {
  return requestResult<Analysis>(text, "/v1/link");
}

export function extractProducts(text: string): Promise<Extraction> {
  return requestResult<Extraction>(text, "/v1/extract-and-link");
}
