import React, { useState } from "react";

export default function AddPatientModal({ onClose, onSubmit }) {
  const [form, setForm] = useState({ name: "", relation: "Self", age: "", blood: "", phone: "" });
  const [error, setError] = useState("");

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((s) => ({ ...s, [name]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!form.name.trim() || !form.age || !form.phone.trim()) {
      setError("Please enter name, age and phone before adding.");
      return;
    }
    onSubmit({ ...form, age: Number(form.age) });
  }

  return (
    <div className="modal-backdrop">
      <section className="modal" role="dialog" aria-modal="true">
        <div className="modal-head">
          <h3>Add family member</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Close">X</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <label className="field"><span>Name</span><input name="name" value={form.name} onChange={handleChange} required /></label>
          <label className="field"><span>Relation</span><input name="relation" value={form.relation} onChange={handleChange} /></label>
          <label className="field"><span>Age</span><input name="age" type="number" value={form.age} onChange={handleChange} required /></label>
          <label className="field"><span>Blood group</span><input name="blood" value={form.blood} onChange={handleChange} /></label>
          <label className="field"><span>Phone</span><input name="phone" value={form.phone} onChange={handleChange} required /></label>
          {error && <p className="error">{error}</p>}
          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button className="btn ghost" type="button" onClick={onClose}>Cancel</button>
            <button className="btn" type="submit">Add member</button>
          </div>
        </form>
      </section>
    </div>
  );
}
