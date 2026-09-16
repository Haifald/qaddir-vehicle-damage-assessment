import { AssessmentWorkspace } from "@/components/assessment-workspace";
import { ShieldIcon } from "@/components/icons";

export default function Home() {
  return (
    <main>
      <div className="utility-bar">
        <div className="utility-inner">
          <span>Qaddir · AI-Assisted Preliminary Vehicle Damage Assessment</span>
          <span className="utility-status"><i /> Human review remains required</span>
        </div>
      </div>

      <header className="site-header">
        <a className="brand-lockup" href="#top" aria-label="Qaddir home">
          <span className="qaddir-mark" aria-hidden="true">
            <i className="ray ray-1" />
            <i className="ray ray-2" />
            <i className="ray ray-3" />
            <b>Q</b>
          </span>
          <span className="qaddir-wordmark">Qaddir</span>
          <span className="brand-divider" aria-hidden="true" />
          <span className="academy-lockup">
            <strong>أكاديمية طويق</strong>
            <small>Tuwaiq Academy</small>
          </span>
          <span className="academy-mark" aria-hidden="true">
            <i /><i /><i />
          </span>
        </a>

        <div className="header-note">
          <ShieldIcon />
          <span>
            <strong>Human-reviewed workflow</strong>
            <small>Structured evidence before reporting</small>
          </span>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="eyebrow">AI-assisted preliminary assessment</div>
          <h1>
            Vehicle damage assessment,
            <span> structured for review.</span>
          </h1>
          <p>
            Qaddir converts vehicle imagery into structured computer-vision findings,
            verifies the evidence, and prepares a preliminary output for qualified human review.
          </p>
          <div className="hero-pills" aria-label="Qaddir capabilities">
            <span>Computer Vision</span>
            <span>Structured CV JSON</span>
            <span>Verification Layer</span>
            <span>Human Review</span>
          </div>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <div className="visual-grid" />
          <div className="scan-frame"><i /><i /><i /><i /></div>
          <div className="damage-card">
            <span>✓</span>
            <div><strong>Assessment workflow</strong><small>Evidence · Verify · Review</small></div>
          </div>
          <div className="visual-car">
            <span className="car-roof" />
            <span className="car-body" />
            <span className="car-window" />
            <span className="wheel wheel-left" />
            <span className="wheel wheel-right" />
          </div>
        </div>
      </section>

      <AssessmentWorkspace />

      <footer>
        <div>
          <strong>Qaddir</strong>
          <span>AI-Assisted Preliminary Vehicle Damage Assessment</span>
        </div>
        <p>Preliminary decision support only · Final decisions remain with qualified human assessors</p>
      </footer>
    </main>
  );
}
