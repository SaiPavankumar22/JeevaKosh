import React from "react";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import Icon, { IconBadge } from "../components/Icon.jsx";
import { Stethoscope, Home } from "lucide-react";

export default function Specialties(props) {
  return (
    <React.Fragment>
      <PageHead eyebrow="Departments" title="Search by specialty" desc={props.selectedHospital ? props.selectedHospital.name : "Choose the care department you need."} icon={Stethoscope} action={<Button variant="ghost" icon={Home} onClick={() => props.navigate("dashboard")}>Back home</Button>} />
      <div className="specialty-grid">
        {props.specialties.map((specialty, index) => (
          <button
            className="specialty-card selectable"
            key={specialty}
            onClick={() => {
              props.setSelectedSpecialty(specialty);
              props.navigate("doctors");
            }}
          >
            <IconBadge icon={props.specialtyIcons ? props.specialtyIcons[specialty] : Stethoscope} className="specialty-icon" />
            <h3>{specialty}</h3>
            <p className="muted">{`${2 + (index % 4)} doctors available today`}</p>
          </button>
        ))}
      </div>
    </React.Fragment>
  );
}
