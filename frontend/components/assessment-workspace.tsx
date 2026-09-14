"use client";

import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import { assessImage, fetchHealth } from "@/lib/api";
import type { ApiError, AssessmentResponse, HealthResponse } from "@/lib/types";
import { ArrowIcon, ImageIcon, ShieldIcon, UploadIcon } from "./icons";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024;

const workflow = [
  ["01", "Image intake", "Format and quality screening"],
  ["02", "Vision analysis", "Damage and part detection"],
  ["03", "Verification", "Evidence and confidence checks"],
  ["04", "Preliminary report", "Grounded assessor summary"],
];

function readable(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function confidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function AssessmentWorkspace() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthFailed, setHealthFailed] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AssessmentResponse | null>(null);
  const [error, setError] = useState<(Error & Partial<ApiError>) | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealthFailed(true));
  }, []);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const readiness = useMemo(() => {
    if (healthFailed) return { label: "API offline", ready: false };
    if (!health) return { label: "Checking pipeline", ready: false };
    return health.status === "ready"
      ? { label: "Pipeline ready", ready: true }
      : { label: "Setup required", ready: false };
  }, [health, healthFailed]);

  function selectFile(nextFile: File | undefined) {
    setResult(null);
    setError(null);
    if (!nextFile) return;
    if (!ACCEPTED_TYPES.includes(nextFile.type)) {
      setError(Object.assign(new Error("Upload a JPEG, PNG, or WebP image."), { code: "invalid_image" }));
      return;
    }
    if (nextFile.size > MAX_BYTES) {
      setError(Object.assign(new Error("The selected image is larger than 10 MB."), { code: "invalid_image" }));
      return;
    }
    setFile(nextFile);
  }

  function onInput(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0]);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  async function analyze() {
    if (!file) {
      setError(Object.assign(new Error("Choose a vehicle image before running analysis."), { code: "no_image" }));
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await assessImage(file));
    } catch (caught) {
      setError(caught as Error & Partial<ApiError>);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="workflow" aria-label="Assessment workflow">
        {workflow.map(([number, title, detail], index) => (
          <div className="workflow-step" key={number}>
            <span>{number}</span>
            <div><strong>{title}</strong><small>{detail}</small></div>
            {index < workflow.length - 1 && <ArrowIcon className="workflow-arrow" />}
          </div>
        ))}
      </section>

      <section className="workspace-shell">
        <div className="section-heading">
          <div>
            <span className="kicker">New assessment</span>
            <h2>Upload vehicle imagery</h2>
          </div>
          <span className={`readiness ${readiness.ready ? "is-ready" : ""}`}>
            <i />{readiness.label}
          </span>
        </div>

        {health?.status === "configuration_required" && (
          <details className="setup-panel">
            <summary>View pipeline readiness</summary>
            <div className="setup-grid">
              {Object.entries(health.components).map(([name, component]) => (
                <div key={name}>
                  <span className={component.ready ? "check" : "pending"}>{component.ready ? "Ready" : "Pending"}</span>
                  <strong>{readable(name)}</strong>
                  <p>{component.detail}</p>
                </div>
              ))}
            </div>
          </details>
        )}

        <div className="upload-grid">
          <div
            className={`dropzone ${dragging ? "is-dragging" : ""} ${preview ? "has-preview" : ""}`}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            {preview ? (
              <>
                {/* Local object URLs are required for immediate upload previews. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={preview} alt="Selected vehicle" className="preview-image" />
                <div className="preview-scrim">
                  <span>{file?.name}</span>
                  <button type="button" onClick={() => inputRef.current?.click()}>Replace image</button>
                </div>
              </>
            ) : (
              <div className="dropzone-content">
                <span className="upload-icon"><UploadIcon /></span>
                <h3>Drop a vehicle image here</h3>
                <p>Use a clear full or medium-distance view for more reliable part identification.</p>
                <button type="button" className="secondary-button" onClick={() => inputRef.current?.click()}>
                  Choose image
                </button>
                <small>JPEG, PNG or WebP · 10 MB maximum</small>
              </div>
            )}
            <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={onInput} hidden />
          </div>

          <aside className="capture-guide">
            <div className="guide-icon"><ImageIcon /></div>
            <h3>Capture guidance</h3>
            <ul>
              <li><i />Keep the affected panel in clear view</li>
              <li><i />Include surrounding vehicle context</li>
              <li><i />Avoid glare, heavy shadow, and blur</li>
            </ul>
            <div className="trust-note">
              <ShieldIcon />
              <p><strong>Evidence first</strong>The report can only use fields accepted by verification.</p>
            </div>
          </aside>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            <strong>{error.code === "cv_pipeline_unavailable" ? "CV pipeline not configured" : "Analysis could not continue"}</strong>
            <p>{error.message}</p>
            {error.code === "cv_pipeline_unavailable" && <small>No assessment result was generated.</small>}
          </div>
        )}

        <div className="action-row">
          <p><ShieldIcon /> Images are processed only for this preliminary assessment.</p>
          <button className="primary-button" type="button" onClick={analyze} disabled={loading || !file}>
            {loading ? <><span className="spinner" />Running analysis</> : <>Run AI analysis<ArrowIcon /></>}
          </button>
        </div>
      </section>

      {result && <AssessmentResult result={result} originalPreview={preview} />}

      {!result && (
        <section className="principles">
          <div><span>01</span><h3>Traceable</h3><p>Every report statement maps back to a structured CV field.</p></div>
          <div><span>02</span><h3>Conservative</h3><p>Contradictions are rejected and uncertainty is made visible.</p></div>
          <div><span>03</span><h3>Human-led</h3><p>The system assists; a qualified assessor makes the final decision.</p></div>
        </section>
      )}
    </>
  );
}

function AssessmentResult({ result, originalPreview }: { result: AssessmentResponse; originalPreview: string | null }) {
  const damageById = new Map(result.cv_output.damage_detections.map((item) => [item.id, item]));
  const partById = new Map(result.cv_output.part_detections.map((item) => [item.id, item]));
  const associations = new Map(result.cv_output.associations.map((item) => [item.damage_id, item]));
  const statusLabel = readable(result.verification.status);

  return (
    <section className="results-shell" aria-live="polite">
      <div className="section-heading results-heading">
        <div><span className="kicker">Assessment {result.analysis_id.slice(0, 8)}</span><h2>Preliminary result</h2></div>
        <span className={`verification-pill status-${result.verification.status}`}><ShieldIcon />{statusLabel}</span>
      </div>

      <div className="evidence-grid">
        <div className="evidence-card">
          <div className="card-label"><span>Visual model result</span><small>Damage · Part</small></div>
          {/* Result imagery comes from the local API or the local upload preview. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={result.overlay_data_url ?? originalPreview ?? ""} alt="Vehicle analysis overlay" />
        </div>
        <div className="metrics-card">
          <div className="metric"><span>Detected damage</span><strong>{result.cv_output.damage_detections.length}</strong></div>
          <div className="metric"><span>Detected parts</span><strong>{result.cv_output.part_detections.length}</strong></div>
          <div className="metric wide"><span>Severity</span><strong className="not-assessed">Not assessed</strong><small>Not produced by the current CV models</small></div>
          <div className="metric wide"><span>Verification status</span><strong>{statusLabel}</strong></div>
        </div>
      </div>

      <div className="findings-card">
        <div className="card-label"><span>Structured findings</span><small>Verified CV contract</small></div>
        {result.cv_output.damage_detections.length === 0 ? (
          <div className="empty-finding">No damage was detected in this image. This does not establish that the vehicle is undamaged.</div>
        ) : (
          <div className="findings-table">
            <div className="table-row table-head"><span>Damage type</span><span>Vehicle part</span><span>AI confidence</span><span>Link confidence</span></div>
            {[...damageById.values()].map((damage) => {
              const association = associations.get(damage.id);
              const part = association?.part_id ? partById.get(association.part_id) : null;
              return (
                <div className="table-row" key={damage.id}>
                  <span data-label="Damage type">{readable(damage.class)}</span>
                  <span data-label="Vehicle part">{part ? readable(part.class) : "Not determined"}</span>
                  <span data-label="AI confidence"><ConfidenceBar value={damage.confidence} /></span>
                  <span data-label="Link confidence">{association ? confidence(association.confidence) : "—"}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {result.verification.issues.length > 0 && (
        <div className="review-card">
          <div><span className="review-symbol">!</span><div><strong>Manual review required</strong><p>The verification layer identified items that need assessor attention.</p></div></div>
          <ul>{result.verification.issues.map((issue) => <li key={`${issue.code}-${issue.path}`}>{issue.message}</li>)}</ul>
        </div>
      )}

      <div className="report-grid">
        <article className="report-card">
          <div className="card-label"><span>Preliminary assessment</span><small>{readable(result.report.status)}</small></div>
          {result.report.text ? <pre>{result.report.text}</pre> : <p className="unavailable-copy">{result.report.message}</p>}
        </article>
        <aside className="recommendation-card">
          <span>Recommendation</span>
          <p>{result.recommendation}</p>
          <hr />
          <small>{result.disclaimer}</small>
        </aside>
      </div>
    </section>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  return <span className="confidence"><span><i style={{ width: `${value * 100}%` }} /></span><b>{confidence(value)}</b></span>;
}
