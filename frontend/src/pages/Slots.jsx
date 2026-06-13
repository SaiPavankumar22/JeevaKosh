import React from "react";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import Icon from "../components/Icon.jsx";
import { CalendarCheck, Clock3 as ClockIcon, Siren, Activity } from "lucide-react";

export default function Slots(props) {
  const doctor = props.selectedDoctor || (props.doctors && props.doctors[0]);
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const slots = ["09:00 AM", "10:30 AM", "12:15 PM", "03:00 PM", "05:45 PM"];

  function showToast(message) {
    props.setToast(message);
    window.setTimeout(() => props.setToast(""), 2800);
  }

  return (
    <React.Fragment>
      <PageHead eyebrow="Appointment" title={doctor ? doctor.name : "Appointment"} desc={doctor ? `${doctor.specialty} | ${props.selectedHospital ? props.selectedHospital.name : "Jeevakosh network"}` : ""} icon={CalendarCheck} action={<Button variant="ghost" icon={CalendarCheck} onClick={() => props.navigate("doctors")}>Change doctor</Button>} />
      <section className="slot-panel">
        <div className="panel">
          <div className="panel-head"><h2><Icon icon={CalendarCheck} />Available calendar</h2><span className="badge">June 2026</span></div>
          <div className="calendar">{days.map((day, index) => <button key={day} className={`day ${props.selectedDay === index ? "active" : ""}`} onClick={() => props.setSelectedDay(index)}><strong>{day}</strong><span>{`${15 + index} Jun`}</span></button>)}</div>
        </div>
        <div className="panel">
          <div className="panel-head"><h2><Icon icon={ClockIcon} />Available slots</h2><span className="badge pulse-badge"><Icon icon={Activity} size={16} />Clinic live</span></div>
          <div className="slots">{slots.map(slot => <button key={slot} className={`slot ${props.selectedSlot === slot ? "active" : ""}`} onClick={() => props.setSelectedSlot(slot)}>{slot}</button>)}</div>
        </div>
        <div className="emergency-panel">
          <div><h2><Icon icon={Siren} />Serious case support</h2><p>For severe chest pain, breathing difficulty, major bleeding, sudden weakness, fainting, or uncontrolled pain, use emergency booking and contact local emergency services immediately.</p></div>
          <div className="emergency-actions"><Button variant="warn" icon={Siren} onClick={() => showToast(`Emergency request sent to ${doctor.name}'s care desk.`)}>Emergency appointment</Button><Button icon={CalendarCheck} onClick={() => showToast(`Appointment booked with ${doctor.name} at ${props.selectedSlot}.`)}>Book selected slot</Button></div>
        </div>
      </section>
    </React.Fragment>
  );
}
