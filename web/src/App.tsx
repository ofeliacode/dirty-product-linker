import { FormEvent, useState } from "react";
import { analyzeProduct, extractProducts } from "./api";
import type { Analysis, Candidate, Extraction } from "./types";

const EXAMPLES = [
  "ищу 15pm на 256",
  "нужен самсунь s24 ultra",
  "сони наушники xm5",
  "айфон эир",
  "нужен айфон 15 про макс и наушники sony xm5",
  "какой-нибудь хороший телефон",
];

const CATEGORY_NAMES: Record<string, string> = {
  smartphone: "Smartphone",
  laptop: "Laptop",
  headphones: "Headphones",
  television: "Television",
  home_appliance: "Home appliance",
};

function percent(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function abstentionTitle(analysis: Analysis): string {
  if (analysis.reason === "brand_not_in_catalog" && analysis.detected_brand) {
    return `${analysis.detected_brand} is not in this catalog`;
  }
  if (analysis.reason === "ambiguous_candidates") return "Multiple close matches";
  if (analysis.reason === "missing_product_identity") return "Not enough product identity";
  return "No reliable catalog match";
}

function CandidateRow({ candidate, rank }: { candidate: Candidate; rank: number }) {
  return (
    <li className="candidate">
      <span className="candidate__rank">{String(rank).padStart(2, "0")}</span>
      <div className="candidate__body">
        <div className="candidate__title-row">
          <span>{candidate.brand} {candidate.model}</span>
          <strong>{percent(candidate.score)}</strong>
        </div>
        <div className="score-track" aria-hidden="true">
          <span style={{ width: percent(candidate.score) }} />
        </div>
        <p>Matched <code>{candidate.matched_surface}</code></p>
      </div>
    </li>
  );
}

export function App() {
  const [text, setText] = useState(EXAMPLES[0]);
  const [mode, setMode] = useState<"single" | "multiple">("single");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [extraction, setExtraction] = useState<Extraction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!text.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      if (mode === "multiple") {
        setExtraction(await extractProducts(text.trim()));
        setAnalysis(null);
      } else {
        setAnalysis(await analyzeProduct(text.trim()));
        setExtraction(null);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unexpected error.");
    } finally {
      setLoading(false);
    }
  }

  function chooseExample(example: string) {
    setText(example);
    setMode(example.includes(" и ") ? "multiple" : "single");
    setAnalysis(null);
    setExtraction(null);
    setError(null);
  }

  function chooseMode(nextMode: "single" | "multiple") {
    setMode(nextMode);
    setAnalysis(null);
    setExtraction(null);
    setError(null);
  }

  return (
    <div className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Dirty Product Linker home">
          <span className="brand__mark">DPL</span>
          <span>Dirty Product Linker</span>
        </a>
        <div className="runtime"><span /> Local inference</div>
      </header>

      <main>
        <section className="intro">
          <p className="eyebrow">EXPLAINABLE ENTITY LINKING · DEMO 01</p>
          <h1>Resolve messy<br />product text.</h1>
          <p className="lede">
            Turn slang, abbreviations, and misspelled model names into canonical catalog records—without hiding the ranking evidence.
          </p>
        </section>

        <div className="workspace">
          <form className="query-panel" onSubmit={submit}>
            <div className="panel-heading">
              <span className="step">01</span>
              <div>
                <h2>Raw customer message</h2>
                <p>Russian, English, or mixed text</p>
              </div>
            </div>
            <div className="mode-switch" aria-label="Resolution mode">
              <button className={mode === "single" ? "is-active" : ""} type="button" onClick={() => chooseMode("single")}>Single mention</button>
              <button className={mode === "multiple" ? "is-active" : ""} type="button" onClick={() => chooseMode("multiple")}>Multiple mentions</button>
            </div>
            <label htmlFor="product-query">Product mention</label>
            <textarea
              id="product-query"
              value={text}
              maxLength={500}
              onChange={(event) => setText(event.target.value)}
              placeholder="Example: ищу 15pm на 256"
              rows={6}
            />
            <div className="input-meta">
              <span>{text.length} / 500</span>
              <span>No data is stored</span>
            </div>
            <button className="primary" type="submit" disabled={!text.trim() || loading}>
              {loading ? "Resolving…" : mode === "multiple" ? "Extract and resolve" : "Resolve product"}
              <span aria-hidden="true">→</span>
            </button>
            {error && <p className="error" role="alert">{error}</p>}

            <div className="examples">
              <p>Try a noisy example</p>
              <div>
                {EXAMPLES.map((example) => (
                  <button key={example} type="button" onClick={() => chooseExample(example)}>
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </form>

          <section className="result-panel" aria-live="polite" aria-busy={loading}>
            <div className="panel-heading">
              <span className="step">02</span>
              <div>
                <h2>Resolution</h2>
                <p>Decision and ranking evidence</p>
              </div>
            </div>

            {!analysis && !extraction && !loading && (
              <div className="empty-state">
                <span>↳</span>
                <p>Submit a message to inspect the selected catalog record and its nearest candidates.</p>
              </div>
            )}

            {loading && <div className="loading-state"><span /><p>Comparing catalog surfaces…</p></div>}

            {analysis && !loading && (
              <div className="result-content">
                <div className={`decision decision--${analysis.status}`}>
                  <div className="decision__label">
                    <span>{analysis.status === "linked" ? "MATCH FOUND" : "SAFE ABSTENTION"}</span>
                    <strong>{percent(analysis.confidence)}</strong>
                  </div>
                  {analysis.selected_product ? (
                    <>
                      <h3>{analysis.selected_product.brand}<br />{analysis.selected_product.model}</h3>
                      <div className="facts">
                        <span>{CATEGORY_NAMES[analysis.selected_product.category] ?? analysis.selected_product.category}</span>
                        <code>{analysis.selected_product.product_id}</code>
                      </div>
                    </>
                  ) : (
                    <h3>{abstentionTitle(analysis)}</h3>
                  )}
                </div>

                <div className="ranking">
                  <div className="ranking__heading">
                    <h3>Candidate ranking</h3>
                    <span>TOP {analysis.candidates.length}</span>
                  </div>
                  <ol>
                    {analysis.candidates.map((candidate, index) => (
                      <CandidateRow candidate={candidate} rank={index + 1} key={candidate.product_id} />
                    ))}
                  </ol>
                </div>

                <div className="telemetry">
                  <span>Decision <strong>{analysis.decision_source}</strong></span>
                  <span>Latency <strong>{analysis.processing_ms.toFixed(2)} ms</strong></span>
                  <span>Model <strong>{analysis.model_version}</strong></span>
                  <span>Catalog <strong>{analysis.catalog_version}</strong></span>
                </div>
              </div>
            )}

            {extraction && !loading && (
              <div className="mention-results">
                <div className="mention-results__heading">
                  <span>EXTRACTED MENTIONS</span>
                  <strong>{extraction.mentions.length}</strong>
                </div>
                {extraction.mentions.length === 0 ? (
                  <div className="decision decision--unknown"><h3>No explicit catalog mentions</h3></div>
                ) : extraction.mentions.map((mention) => (
                  <article className="mention-card" key={`${mention.start}-${mention.end}`}>
                    <div className="mention-card__source">
                      <span>“{mention.text}”</span>
                      <code>{mention.start}:{mention.end}</code>
                    </div>
                    <h3>{mention.result.selected_product?.brand} {mention.result.selected_product?.model}</h3>
                    <div className="facts">
                      <span>{percent(mention.result.confidence)} confidence</span>
                      <code>{mention.result.product_id}</code>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </main>

      <footer>
        <p>Portfolio research project · deterministic baseline · inspectable decisions</p>
        <a href="https://github.com/ofeliacode/dirty-product-linker">View source ↗</a>
      </footer>
    </div>
  );
}
