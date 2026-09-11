import { ArrowLeft,Pause, Play } from "lucide-react";
import BreathIcon from "./icons/BreathIcon";
import { useEffect, useState } from "react";

const phases = [
  {
    name: "Breathe in",
    duration: 4,
  },
  {
    name: "Hold",
    duration: 4,
  },
  {
    name: "Breathe out",
    duration: 6,
  },
];

const CIRCLE_RADIUS = 82;
const CIRCLE_LENGTH = 2 * Math.PI * CIRCLE_RADIUS;

export default function BreathingGuide({ onBack }) {
  const [running, setRunning] = useState(false);
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState(
    phases[0].duration
  );
  const [progress, setProgress] = useState(0);

  const phase = phases[phaseIndex];

  useEffect(() => {
    if (!running) return;

    const startTime = Date.now();
    const duration = phase.duration * 1000;

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;

      const currentProgress = Math.min(
        elapsed / duration,
        1
      );

      setProgress(currentProgress);

      setSecondsLeft(
        Math.max(
          0,
          Math.ceil((duration - elapsed) / 1000)
        )
      );

      if (elapsed >= duration) {
        clearInterval(timer);

        const nextIndex =
          (phaseIndex + 1) % phases.length;

        setPhaseIndex(nextIndex);
        setSecondsLeft(phases[nextIndex].duration);
        setProgress(0);
      }
    }, 50);

    return () => clearInterval(timer);
  }, [running, phaseIndex]);

  function startBreathing() {
    setPhaseIndex(0);
    setSecondsLeft(phases[0].duration);
    setProgress(0);
    setRunning(true);
  }

  function pauseBreathing() {
    setRunning(false);
    setPhaseIndex(0);
  setSecondsLeft(phases[0].duration);
  setProgress(0);
  }

  return (
    <section className="relative h-full overflow-hidden">
      {/* Soft background */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_38%,rgba(211,228,217,0.7),transparent_48%)]" />
       
        {/* Back to conversation */}
        <button
          type="button"
          onClick={onBack}
          className="absolute left-6 top-6 z-10 flex items-center gap-2 rounded-wa px-2 py-2 text-sm text-wa-muted transition hover:bg-wa-sidebar/60 hover:text-wa-text"
        >
          <ArrowLeft size={17} strokeWidth={1.8} />
          <span>Back to conversation</span>
        </button>
        <div className="relative mx-auto h-full max-w-[1000px] px-6">

        {/* Main content */}
        <div className="flex h-full items-center justify-center">
          <div className="w-full max-w-[760px] text-center">

            {/* Breathing icon */}
            <div className="mx-auto flex h-12 w-12 items-center justify-center text-wa-accent">
            <BreathIcon
  size={40}
  strokeWidth={1.8}
/>
            </div>

            {/* Label */}
            <div className="mt-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-wa-accent">
              Take a Breath
            </div>

            {/* Heading */}
            <h1 className="mt-3 text-[clamp(34px,4vw,48px)] font-semibold leading-tight tracking-[-0.04em] text-wa-text">
              Slow down for a moment.
            </h1>

            <p className="mx-auto mt-4 max-w-[540px] text-[15px] leading-7 text-wa-muted">
              Follow the circle and let your breathing settle into
              a slower rhythm.
            </p>

            {/* Progress circle */}
            <div className="mx-auto mt-14 flex h-[250px] w-[250px] items-center justify-center">
              <div className="relative flex h-[190px] w-[190px] items-center justify-center">

                <svg
                  className="absolute inset-0 h-full w-full -rotate-90"
                  viewBox="0 0 190 190"
                >
                  {/* Empty circle */}
                  <circle
                    cx="95"
                    cy="95"
                    r={CIRCLE_RADIUS}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-wa-border"
                  />

                  {/* Progress circle */}
                  <circle
                    cx="95"
                    cy="95"
                    r={CIRCLE_RADIUS}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    className="text-wa-accent"
                    strokeDasharray={CIRCLE_LENGTH}
                    strokeDashoffset={
                      CIRCLE_LENGTH *
                      (1 - progress)
                    }
                  />
                </svg>

                {/* Phase information */}
                <div className="relative z-10 flex flex-col items-center text-center">

                  <div className="text-[16px] font-medium leading-6 text-wa-text">
                    {running ? phase.name : "Ready"}
                  </div>

                  <div className="mt-1 text-[26px] font-medium leading-8 text-wa-accent">
                    {running ? secondsLeft : "—"}
                  </div>

                </div>
              </div>
            </div>

            {/* Control */}
            <div className="mt-8 flex justify-center">
              {!running ? (
                <button
                  type="button"
                  onClick={startBreathing}
                  className="flex items-center gap-2 rounded-wa bg-wa-sidebar px-6 py-3 text-sm font-medium text-wa-text transition hover:bg-wa-accentSoft/50"
                >
                  <Play size={15} strokeWidth={1.8} />
                  Start breathing
                </button>
              ) : (
                <button
                  type="button"
                  onClick={pauseBreathing}
                  className="flex items-center gap-2 rounded-wa border border-wa-border bg-wa-surface px-6 py-3 text-sm font-medium text-wa-text transition hover:bg-wa-sidebar"
                >
                  <Pause size={15} strokeWidth={1.8} />
                  Pause
                </button>
              )}
            </div>

            {/* Phase guide */}
            <p className="mt-5 text-[11px] text-wa-muted">
              Breathe in · Hold · Breathe out
            </p>

          </div>
        </div>
      </div>
    </section>
  );
}