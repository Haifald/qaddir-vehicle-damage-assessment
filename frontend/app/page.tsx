import { AssessmentWorkspace } from "@/components/assessment-workspace";

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Qaddir home">
          <span className="brand-mark" aria-hidden="true">ق</span>
          <span>
            <strong>Qaddir</strong>
            <small>Vehicle Intelligence</small>
          </span>
        </a>
        <div className="header-note">
          <span className="status-dot" />
          Human-reviewed assessment
        </div>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow">AI-assisted inspection workflow</div>
        <h1>Clear evidence.<br />Measured conclusions.</h1>
        <p>
          Qaddir turns vehicle imagery into a traceable preliminary damage record,
          with verification before any report reaches an assessor.
        </p>
      </section>

      <AssessmentWorkspace />

      <footer>
        <span>Qaddir graduation project</span>
        <span>Preliminary results · Final decisions remain with qualified assessors</span>
      </footer>
    </main>
  );
}
