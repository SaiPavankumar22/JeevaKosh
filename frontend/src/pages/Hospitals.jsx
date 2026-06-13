import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import Icon from "../components/Icon.jsx";
import { createHospital, deleteHospital } from "../api";
import { Hospital, MapPin, Home, Plus, Trash2 } from "lucide-react";

export default function Hospitals(props) {
  const [name, setName] = useState("");
  const [showForm, setShowForm] = useState(false);
  const qc = useQueryClient();
  const hospitals = props.apiHospitals ?? [];

  const createMutation = useMutation({
    mutationFn: () => createHospital(name.trim()),
    onSuccess: (hospital) => {
      qc.invalidateQueries({ queryKey: ["hospitals"] });
      setName("");
      setShowForm(false);
      props.setActiveHospital(hospital);
      props.navigate("hospital-vault");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteHospital(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hospitals"] }),
  });

  return (
    <React.Fragment>
      <PageHead
        eyebrow="Care network"
        title="Your hospitals"
        desc="Manage hospital folders for prescriptions, reports, and OCR extraction."
        icon={Hospital}
        action={
          <Button variant="ghost" icon={Home} onClick={() => props.navigate("dashboard")}>
            Back home
          </Button>
        }
      />

      <div className="panel" style={{ marginBottom: "1rem" }}>
        <Button icon={Plus} onClick={() => setShowForm((v) => !v)}>
          Add hospital
        </Button>
        {showForm && (
          <form
            className="form-grid"
            style={{ marginTop: "1rem" }}
            onSubmit={(e) => {
              e.preventDefault();
              if (name.trim()) createMutation.mutate();
            }}
          >
            <label className="field full">
              <span>Hospital name</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Apollo Hospital"
                required
              />
            </label>
            <Button type="submit" disabled={createMutation.isPending}>
              Create
            </Button>
          </form>
        )}
      </div>

      {hospitals.length === 0 ? (
        <div className="panel">
          <p className="muted">No hospitals yet. Add one to start uploading medical documents.</p>
        </div>
      ) : (
        <div className="hospital-grid">
          {hospitals.map((hospital) => (
            <article className="hospital-card" key={hospital.id}>
              <button
                className="selectable"
                style={{ textAlign: "left", width: "100%" }}
                onClick={() => {
                  props.setActiveHospital(hospital);
                  props.navigate("hospital-vault");
                }}
              >
                <div className="hospital-score">
                  {hospital.total_prescriptions + hospital.total_reports}
                </div>
                <span className="badge">
                  <Icon icon={MapPin} size={15} />
                  Medical vault
                </span>
                <h3>{hospital.name}</h3>
                <p className="muted">
                  {hospital.total_prescriptions} prescriptions · {hospital.total_reports} reports
                </p>
                <p>Created {new Date(hospital.created_at).toLocaleDateString()}</p>
              </button>
              <button
                className="icon-btn"
                style={{ marginTop: "0.5rem" }}
                onClick={() => {
                  if (confirm(`Delete "${hospital.name}" and all its documents?`)) {
                    deleteMutation.mutate(hospital.id);
                  }
                }}
                aria-label="Delete hospital"
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      )}
    </React.Fragment>
  );
}
