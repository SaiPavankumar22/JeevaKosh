import React from "react";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import Icon, { IconBadge } from "../components/Icon.jsx";
import { Stethoscope, CalendarCheck, Search } from "lucide-react";

export default function Doctors(props) {
  const list = (props.doctors || []).filter((doctor) => doctor.specialty === props.selectedSpecialty);
  const shown = list.length ? list : (props.doctors || []).slice(0, 3).map((doctor) => ({ ...doctor, specialty: props.selectedSpecialty || "General Medicine" }));

  return (
    <React.Fragment>
      <PageHead eyebrow="Doctors" title={props.selectedSpecialty || "Available doctors"} desc={props.selectedHospital ? props.selectedHospital.name : "Jeevakosh network"} icon={Stethoscope} action={<Button variant="ghost" icon={Search} onClick={() => props.navigate("specialties")}>Change specialty</Button>} />
      <div className="doctor-grid">
        {shown.map((doctor) => (
          <article className="doctor-card" key={doctor.name}>
            <div className={`doctor-photo doctor-portrait portrait-${doctor.photoIndex ?? 0}`} role="img" aria-label={`Portrait of ${doctor.name}`}>
              <span className="doctor-rating-chip">{`${doctor.rating} rating`}</span>
            </div>
            <div className="doctor-body">
              <span className="badge"><Icon icon={props.specialtyIcons ? props.specialtyIcons[doctor.specialty] : Stethoscope} size={15} />{doctor.specialty}</span>
              <h3>{doctor.name}</h3>
              <p className="muted">{`${doctor.exp} experience | next slot ${doctor.next}`}</p>
              <p>Profile includes availability, specialty, hospital context, and emergency appointment access.</p>
              <Button icon={CalendarCheck} onClick={() => { props.setSelectedDoctor(doctor); props.setSelectedSlot(doctor.next); props.navigate("slots"); }}>View slots</Button>
            </div>
          </article>
        ))}
      </div>
    </React.Fragment>
  );
}
