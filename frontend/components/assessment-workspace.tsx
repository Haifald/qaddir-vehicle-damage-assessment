"use client";

import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import { assessImage, fetchHealth } from "@/lib/api";
import { clientError, describeError, type UserFacingError } from "@/lib/errors";
import { readable } from "@/lib/format";
import type { AssessmentResponse, HealthResponse } from "@/lib/types";
import { AssessmentResult } from "./assessment-result";
import { ArrowIcon, ImageIcon, ShieldIcon, UploadIcon } from "./icons";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024;

const workflow = [
  ["01", "Input image", "Vehicle photo from user"],
  ["02", "CV inference", "Damage and vehicle-part detection"],
  ["03", "Damage-to-part", "Evidence association"],
  ["04", "Verification", "Schema and confidence checks"],
  ["05", "Review output", "Human-reviewable result"],
];

export function AssessmentWorkspace() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthFailed, setHealthFailed] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AssessmentResponse | null>(null);
  const [error, setError] = useState<UserFacingError | null>(null);
  // Synchronous guard: `loading` state updates are async, so a fast double click
  // could otherwise start two requests before the button re-renders as disabled.
  const inFlight = useRef(false);

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
    if (inFlight.current) return;
    setResult(null);
    setError(null);
    if (!nextFile) return;
    if (!ACCEPTED_TYPES.includes(nextFile.type)) {
      setError(clientError("invalid_image", "Upload a JPEG, PNG, or WebP image."));
      return;
    }
    if (nextFile.size > MAX_BYTES) {
      setError(clientError("invalid_image", "The selected image is larger than 10 MB."));
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
    if (inFlight.current) return;
    if (!file) {
      setError(clientError("no_image", "Choose a vehicle image before running analysis."));
      return;
    }
    inFlight.current = true;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await assessImage(file));
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      inFlight.current = false;
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
            <h2>Vehicle image intake</h2>
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
            aria-busy={loading}
            onDragOver={(event) => { event.preventDefault(); if (!loading) setDragging(true); }}
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
                  <button type="button" onClick={() => inputRef.current?.click()} disabled={loading}>Replace image</button>
                </div>
              </>
            ) : (
              <div className="dropzone-content">
                <span className="upload-icon"><UploadIcon /></span>
                <h3>Upload a vehicle image</h3>
                <p>Provide a clear vehicle image so damage and vehicle-part evidence can be assessed consistently.</p>
                <button type="button" className="secondary-button" onClick={() => inputRef.current?.click()}>
                  Select image
                </button>
                <small>JPEG, PNG or WebP · 10 MB maximum</small>
              </div>
            )}
            <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={onInput} disabled={loading} hidden />
          </div>

          <aside className="capture-guide">
            <div className="guide-icon"><ImageIcon /></div>
            <h3>Image quality guidance</h3>
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
            <strong>{error.title}</strong>
            <p>{error.message}</p>
            {error.note && <small>{error.note}</small>}
          </div>
        )}

        <div className="action-row">
          <p><ShieldIcon /> Images are processed only for this preliminary assessment.</p>
          <button className="primary-button" type="button" onClick={analyze} disabled={loading || !file}>
            {loading ? <><span className="spinner" />Running analysis</> : <>Start assessment<ArrowIcon /></>}
          </button>
        </div>
      </section>

      {loading && <AssessmentLoading />}

      {result && !loading && <AssessmentResult result={result} originalPreview={preview} />}

      {!result && !loading && (
        <section className="principles">
          <div><span>01</span><h3>Traceable</h3><p>Every report statement maps back to a structured CV field.</p></div>
          <div><span>02</span><h3>Conservative</h3><p>Contradictions are rejected and uncertainty is made visible.</p></div>
          <div><span>03</span><h3>Human-led</h3><p>The system assists; a qualified assessor makes the final decision.</p></div>
        </section>
      )}
    </>
  );
}

function AssessmentLoading() {
  return (
    <section className="results-shell loading-shell" role="status" aria-live="polite" aria-busy="true">
      <span className="spinner spinner-violet" aria-hidden="true" />
      <div>
        <span className="kicker">Assessment in progress</span>
        <h2>Running analysis</h2>
        <p>
          The image is being processed by the computer-vision models, then damage-to-part association and
          verification run on the structured result. Results will appear here when processing finishes.
        </p>
      </div>
    </section>
  );
}
