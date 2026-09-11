import { useId } from "react";

export default function BreathIcon({
  size = 24,
  noseColor = "#31402A",
  breathColor = "#57784A",
  strokeWidth = 2,
  className = "",
  ...rest
}) {
  const markerId = useId();

  return (
    <svg
      width={size}
      height={size}
      viewBox="-8 -26 34 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="Take a breath"
      {...rest}
    >
      <defs>
        <marker
          id={markerId}
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path
            d="M2 1L8 5L2 9"
            fill="none"
            stroke={breathColor}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </marker>
      </defs>

      {/* Nose contour */}
      <path
        d="M -2,-22 C 6,-16 12,-6 10,2 C 9,7 4,9 0,7 C -4,5 -3,0 1,1 C 4,2 3,6 -1,6"
        stroke={noseColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />

      {/* Exhale swirl */}
      <path
        d="M 10,2 Q 18,5 21,12"
        stroke={breathColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        markerEnd={`url(#${markerId})`}
      />
    </svg>
  );
}