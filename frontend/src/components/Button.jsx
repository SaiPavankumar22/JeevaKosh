import React from "react";
import Icon from "./Icon.jsx";

export default function Button({ children, variant = "primary", type = "button", icon, onClick }) {
  return (
    <button className={`btn ${variant}`} type={type} onClick={onClick}>
      {icon && <Icon icon={icon} />}
      {children}
    </button>
  );
}
