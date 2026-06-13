import React from "react";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import Icon, { IconBadge } from "../components/Icon.jsx";
import { Users, UserRoundPlus, UserRound } from "lucide-react";

export default function Patients(props) {
  return (
    <React.Fragment>
      <PageHead eyebrow="Family profiles" title="Select patient" desc="Continue with an existing family member or add a new patient profile." icon={Users} action={<Button icon={UserRoundPlus} onClick={props.addPatient}>Add family member</Button>} />
      <div className="patient-grid">
        {props.patients.map((patient) => (
          <button
            className="patient-card selectable"
            key={patient.id}
            onClick={() => {
              props.setSelectedPatient(patient);
              props.navigate("dashboard");
            }}
          >
            <span className="avatar"><UserRound size={22} strokeWidth={2.1} aria-hidden /></span>
            <div>
              <h3>{patient.name}</h3>
              <p className="muted">{`${patient.relation} | ${patient.age} years | ${patient.blood}`}</p>
              <p>{patient.phone}</p>
            </div>
            <span className="badge">{patient.risk}</span>
          </button>
        ))}
      </div>
    </React.Fragment>
  );
}
