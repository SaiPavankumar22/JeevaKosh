import React from "react";
import Brand from "../components/Brand.jsx";
import Button from "../components/Button.jsx";
import Icon, { IconBadge, HeartPulse } from "../components/Icon.jsx";
import { ClipboardList, CalendarCheck, FileText, Microscope, Siren } from "lucide-react";

function Metric({ value, label, icon }) {
  return (
    <div className="metric">
      <Icon icon={icon ?? null} />
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function FlashCard({ icon, title, body }) {
  return (
    <article className="flash-card">
      <IconBadge icon={icon} className="feature-icon" />
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}

function Carousel({ slide, setSlide }) {
  const slides = [
    <img src="assets/jeevakosh-care-platform.png" alt="Jeevakosh care platform dashboard" />,
    <div className="slide-content">
      <span>Smart Timeline</span>
      <h3>Reports, prescriptions, bills, and visits in one view.</h3>
      <p>Records stay tied to the right family member and the right hospital visit.</p>
    </div>,
    <div className="slide-content">
      <span>Care Booking</span>
      <h3>Select hospital, specialty, doctor, and slot.</h3>
      <p>Emergency priority is available for serious cases that need faster attention.</p>
    </div>,
  ];

  return (
    <div className="carousel">
      {slides.map((content, index) => (
        <div key={index} className={`slide ${slide === index ? "active" : ""} ${index ? "synthetic" : ""}`}>{content}</div>
      ))}
      <div className="carousel-status">
        <span>{<HeartPulse />} Next appointment</span>
        <strong>10:30 AM</strong>
        <small>Gastroenterology review</small>
      </div>
      <div className="dots">
        {slides.map((_, index) => (
          <button key={index} className={`dot ${slide === index ? "active" : ""}`} onClick={() => setSlide(index)} aria-label={`Show slide ${index + 1}`} />
        ))}
      </div>
    </div>
  );
}

export default function Landing({ slide, setSlide, openAuth, visitorCards, features, recordTypes, trustPoints, useCases, doctors, faqs, articleCards, visitorIcons, featureIcons, recordIcons, metricIcons, trustIcons }) {
  return (
    <div className="site-shell landing-redesign">
      <div className="notice-bar">
        <span>Learn what to keep ready before an emergency visit.</span>
        <button onClick={() => openAuth("signup")}>Start health vault</button>
      </div>
      <header className="topbar">
        <Brand />
        <nav className="nav">
          <a href="#services">Online Services</a>
          <a href="#vault">Vault</a>
          <a href="#doctors">Doctors</a>
          <a href="#security">Security</a>
          <a href="#faq">FAQ</a>
        </nav>
        <div className="actions">
          <Button variant="ghost" onClick={() => openAuth("login")}>Login</Button>
          <Button onClick={() => openAuth("signup")}>Sign up</Button>
        </div>
      </header>
      <main>
        <section className="hero landing-hero">
          <div className="hero-copy">
            <div className="hero-kicker"><HeartPulse />Family health records, finally in one place</div>
            <h1>Jeevakosh</h1>
            <p className="lead">A calm digital health vault for patient profiles, hospital visits, diagnostics, prescriptions, bills, symptoms, appointments, and emergency details.</p>
            <div className="hero-actions">
              <Button onClick={() => openAuth("signup")}>Create account</Button>
              <Button variant="soft" onClick={() => openAuth("login")} >Continue with OTP</Button>
            </div>
            <article className="location-card">
              <div>
                <span className="eyebrow">Find care nearby</span>
                <h3>Choose a hospital, specialty, and slot with patient history attached.</h3>
              </div>
              <button onClick={() => openAuth("login")} aria-label="Find care">→</button>
            </article>
            <div className="care-ribbon" aria-label="Jeevakosh care highlights">
              {['Reports synced','OTP secured','Family ready','Slots available'].map(item => <span key={item}><HeartPulse />{item}</span>)}
            </div>
            <div className="hero-trust-row">
              {[ [ClipboardList, 'Patient timeline'], [CalendarCheck, 'Doctor booking'], [FileText, 'Reports vault'] ].map(([IconComp, item]) => <span key={item}><IconComp {...{size:22, strokeWidth:2.1}} />{item}</span>)}
            </div>
          </div>
          <div className="product-showcase">
            <Carousel slide={slide} setSlide={setSlide} />
            <div className="showcase-strip">
              <article><CalendarCheck size={21} strokeWidth={2.1} /><strong>Next visit</strong><span>Gastroenterology review</span></article>
              <article><Microscope size={21} strokeWidth={2.1} /><strong>Latest upload</strong><span>Liver function panel</span></article>
              <article><Siren size={21} strokeWidth={2.1} /><strong>Emergency</strong><span>Blood group B+</span></article>
            </div>
          </div>
        </section>
        <section className="visitor-strip" id="services">
          {visitorCards.map(([title, body, label]) => (
              <article className="visitor-card" key={title}>
              <IconBadge icon={visitorIcons?.[label] ?? null} className="visitor-icon" />
              <h3>{title}</h3>
              <p>{body}</p>
              <button onClick={() => openAuth('login')}>Learn More</button>
            </article>
          ))}
        </section>
        <section className="landing-metrics">
          <Metric value="360" label="patient profile" icon={metricIcons?.["patient profile"]} />
          <Metric value="OTP" label="mobile-first access" icon={metricIcons?.["mobile-first access"]} />
          <Metric value="24x7" label="emergency path" icon={metricIcons?.["emergency path"]} />
          <Metric value="1" label="family dashboard" icon={metricIcons?.["family dashboard"]} />
        </section>
        <section className="section story-section" id="specs">
          <div className="about-layout">
            <div className="about-visual">
              <img src="assets/jeevakosh-care-platform.png" alt="Jeevakosh app preview" />
              <div><strong>4</strong><span>core care flows</span></div>
            </div>
            <div className="about-copy">
              <span className="eyebrow">About Jeevakosh</span>
              <h2>A patient-centered health vault for every family member</h2>
              <p className="muted">From a first symptom to a hospital visit, Jeevakosh keeps the whole care story connected to the right person.</p>
              <ul className="amenity-list">{['Seamless records timeline','Family member profiles','Specialty-wise doctor discovery','Emergency details ready'].map(item => <li key={item}>{item}</li>)}</ul>
              <Button onClick={() => openAuth('signup')}>More About Jeevakosh</Button>
            </div>
          </div>
        </section>
        <section className="section records-section" id="vault">
          <div className="section-head"><span className="eyebrow">Health vault</span><h2>Store more than reports</h2><p className="muted">Every upload or entry is organized against the right patient, hospital visit, date, and care type.</p></div>
          <div className="record-grid">
            {recordTypes.map(([title, body]) => (
              <article className="record-card" key={title}><IconBadge icon={recordIcons?.[title] ?? null} className="record-icon" /><h3>{title}</h3><p>{body}</p></article>
            ))}
          </div>
        </section>
        <section className="section trust-section" id="security">
          <div className="trust-copy"><span className="eyebrow">Privacy and trust</span><h2>A calmer way to carry medical history.</h2><p>Medical details are stressful when they are scattered across paper files, lab apps, hospital portals, and family phones. Jeevakosh focuses on one searchable family health view.</p></div>
          <div className="trust-grid">{trustPoints.map(([title, body]) => <article key={title} className="trust-card"><span className="badge pulse-badge">{title}</span><p>{body}</p></article>)}</div>
        </section>
        <section className="section usecase-section">
          <div className="section-head"><span className="eyebrow">Family care</span><h2>Made for real household health routines</h2></div>
          <div className="usecase-grid">{useCases.map(([title, body]) => <article key={title} className="usecase-card"><h3>{title}</h3><p>{body}</p></article>)}</div>
        </section>
        <section className="section doctors-preview" id="doctors">
          <div className="section-head"><span className="eyebrow">Doctors</span><h2>Expert doctors for the patients</h2><p className="muted">Preview doctors by specialty and continue to appointment booking after login.</p></div>
          <div className="landing-doctor-grid">{doctors.slice(0,4).map(doctor => <article className="landing-doctor-card" key={doctor.name}><div className={`doctor-photo doctor-portrait portrait-${doctor.photoIndex}`}><span className="doctor-rating-chip">{doctor.rating} rating</span></div><div><span className="badge">{doctor.specialty}</span><h3>{doctor.name}</h3><p>{doctor.exp} experience</p><button onClick={() => openAuth('login')}>Book Appointment</button></div></article>)}</div>
        </section>
        <section className="section landing-faq">
          <div className="section-head" id="faq"><span className="eyebrow">Questions</span><h2>Before you begin</h2></div>
          <div className="faq-grid">{faqs.map(([q,a]) => <article className="faq-card" key={q}><h3>{q}</h3><p>{a}</p></article>)}</div>
          <div className="article-grid">{articleCards.map(([t,b]) => <article className="article-card" key={t}><span>Care Guide</span><h3>{t}</h3><p>{b}</p><button onClick={() => openAuth('signup')}>Read More</button></article>)}</div>
        </section>
        <footer className="landing-footer">
          <Brand light />
          <p>Jeevakosh keeps patient records, appointments, hospitals, reports, bills, and family care context together.</p>
          <div>{['Online Services','Reports','Doctors','Appointments','Privacy'].map(item => <span key={item}>{item}</span>)}</div>
        </footer>
      </main>
    </div>
  );
}
