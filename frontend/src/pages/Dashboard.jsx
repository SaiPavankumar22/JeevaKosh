import React from "react";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import Icon from "../components/Icon.jsx";
import { Home, HeartPulse as HeartPulseIcon, Activity, Users } from "lucide-react";

function Metric({ value, label, IconComp }) {
  return (
    <div className="metric">
      <Icon icon={IconComp} />
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

export default function Dashboard(props) {
  const patient = props.selectedPatient || (props.patients && props.patients[0]);
  function badgeClassFor(title) {
    const key = (title || "").toLowerCase();
    if (key.includes("special")) return "badge-teal";
    if (key.includes("hospital")) return "badge-amber";
    if (key.includes("book") || key.includes("slot")) return "badge-blue";
    if (key.includes("triage") || key.includes("symptom")) return "badge-green";
    if (key.includes("check") || key.includes("rx")) return "badge-indigo";
    if (key.includes("report")) return "badge-teal";
    return "badge-indigo";
  }
  return (
    <React.Fragment>
      <header className="dashboard-header">
        <div>
          <div className="eyebrow small">PATIENT HOME</div>
          <h1 className="patient-name">{patient ? patient.name : "Patient"}</h1>
          <div className="patient-meta muted">{patient ? `${patient.relation} | ${patient.age} years | Blood group ${patient.blood}` : ""}</div>
        </div>
        <div>
          <Button variant="ghost" icon={Users} onClick={() => props.navigate("patients")}>Change patient</Button>
        </div>
      </header>

      <section className="dashboard-top-grid">
        <div className="hero-large">
          <span className="badge pulse-badge"><Icon icon={HeartPulseIcon} size={14} /> Ready for your next visit</span>
          <h2>Explore every part of the health record at your own pace.</h2>
          <p className="muted">Use Jeevakosh to move between hospitals, specialties, appointments, reports, prescriptions and symptoms without losing patient context.</p>
        </div>
        <div className="metrics-cards">
          <div className="metric-card"><strong>{props.apiHospitals?.length ?? 0}</strong><span>hospitals</span></div>
          <div className="metric-card"><strong>{(props.apiHospitals ?? []).reduce((n, h) => n + h.total_prescriptions + h.total_reports, 0)}</strong><span>documents</span></div>
          <div className="metric-card"><strong>{props.selectedPatient ? 1 : 0}</strong><span>active patient</span></div>
        </div>
      </section>
      <section className="feature-explorer">
        <div className="section-head"><span className="eyebrow">FEATURE EXPLORER</span><h3>Choose what you want to do now</h3><div className="all-modules">All modules</div></div>
        <div className="feature-grid">
          {props.features && props.features.map(([title, subtitle, desc]) => (
            <article className="feature-card" key={title}>
              <div className="feature-head">
                <span className={`feature-badge ${badgeClassFor(title)}`}>{title.split(' ')[0]}</span>
                <h4>{title}</h4>
              </div>
              <p className="muted small">{subtitle}</p>
              <p>{desc}</p>
              <div className="feature-foot"><button className="open-pill">Open</button></div>
            </article>
          ))}
        </div>
      </section>

      <section className="home-timeline">
        <div className="section-head"><h3>Recent activity</h3><p className="muted">Chronological timeline of visits, reports and uploads</p></div>
        <div className="timeline-list">
          {props.timeline && props.timeline.map((item) => (
            <article key={item.title} className={`timeline-card ${item.tone}`}>
              <div className="timeline-date">{item.date}</div>
              <div>
                <h4>{item.title}</h4>
                <p className="muted">{item.meta}</p>
              </div>
              <span className="badge">{item.type}</span>
            </article>
          ))}
        </div>
      </section>
    </React.Fragment>
  );
}
