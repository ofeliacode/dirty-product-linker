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
  decision_source: "lexical" | "feature_reranker";
  score: number;
  processing_ms: number;
  catalog_version: string;
  selected_product: ProductSummary | null;
  candidates: Candidate[];
};
