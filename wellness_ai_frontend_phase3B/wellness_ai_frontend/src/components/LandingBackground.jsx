export default function LandingBackground() {
  return (
    <svg
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
      viewBox="0 0 800 420"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d="M0,300 C120,278 240,296 360,278 C480,262 580,286 700,272 C740,267 770,272 800,270 L800,420 L0,420 Z"
        fill="#6E8B54"
        opacity="0.14"
      />
      <path
        d="M0,330 C150,314 300,336 460,320 C580,308 680,326 800,314 L800,420 L0,420 Z"
        fill="#6E8B54"
        opacity="0.20"
      />
      <g opacity="0.28">
        <rect x="150" y="298" width="4" height="22" fill="#7A6A4A" />
        <circle cx="152" cy="292" r="17" fill="#6E8B54" />
      </g>
      <g opacity="0.22">
        <rect x="300" y="290" width="5" height="26" fill="#7A6A4A" />
        <circle cx="302" cy="282" r="21" fill="#6E8B54" />
      </g>
      <g opacity="0.26">
        <rect x="560" y="296" width="4" height="23" fill="#7A6A4A" />
        <circle cx="562" cy="289" r="18" fill="#6E8B54" />
      </g>
      <g opacity="0.20">
        <rect x="660" y="292" width="5" height="25" fill="#7A6A4A" />
        <circle cx="662" cy="284" r="20" fill="#6E8B54" />
      </g>
      <rect x="0" y="405" width="800" height="15" fill="#7A6A4A" opacity="0.08" />
    </svg>
  );
}