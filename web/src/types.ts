export type ProductSummary = {
  product_id: string;
  brand: string;
  model: string;
  category: string;
};

export type Candidate = ProductSummary & {
  score: number;
  matched_surface: string;
};

export type Analysis = {
  text: string;
  status: "linked" | "unknown";
  decision_source: string;
  score: number;
  confidence: number;
  processing_ms: number;
  model_version: string;
  catalog_version: string;
  product_id: string | null;
  category: string | null;
  reason: "brand_not_in_catalog" | "low_score" | "ambiguous_candidates" | "missing_product_identity" | null;
  detected_brand: string | null;
  selected_product: ProductSummary | null;
  candidates: Candidate[];
};
