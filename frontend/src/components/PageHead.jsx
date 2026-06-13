import React from "react";
import { Activity } from "lucide-react";
import Icon from "./Icon.jsx";
import { IconBadge } from "./Icon.jsx";

export default function PageHead({ eyebrow, title, desc, icon, action }) {
  return (
    <div className="app-head">
      <div className="page-title">
        {icon && <IconBadge icon={icon} className="page-icon" />}
        <div>
          <span className="eyebrow">{eyebrow}</span>
          <h1>{title}</h1>
          <p className="muted">{desc}</p>
        </div>
      </div>
      {action}
    </div>
  );
}
