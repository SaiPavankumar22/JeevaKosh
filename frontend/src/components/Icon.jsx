import React from "react";

const iconProps = { size: 22, strokeWidth: 2.1, "aria-hidden": true };

export default function Icon({ icon: IconComponent, size = 22 }) {
  return IconComponent ? <IconComponent {...iconProps} size={size} /> : null;
}

export function IconBadge({ icon, className }) {
  return <span className={className}><Icon icon={icon} /></span>;
}

export function HeartPulse() {
  return (
    <span className="heart-pulse" aria-hidden="true">
      <span className="heart-core" />
    </span>
  );
}
