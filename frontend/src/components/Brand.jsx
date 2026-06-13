import React from "react";

export default function Brand({ light = false }) {
  return (
    <div className={`brand ${light ? "light" : ""}`}>
      <span className="mark">
        <img src="assets/logo.png" alt="Jeevakosh logo" className="brand-logo" />
      </span>
      <span>Jeevakosh</span>
    </div>
  );
}
