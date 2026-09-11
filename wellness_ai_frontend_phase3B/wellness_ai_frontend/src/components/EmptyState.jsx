import { ArrowUp, Mic } from "lucide-react";
import BreathIcon from "./icons/BreathIcon";
import { useEffect, useRef, useState } from "react";
import LandingBackground from "./LandingBackground";

const suggestions = ["Managing stress", "Ways to cope", "Better sleep"];

export default function EmptyState({
  value,
  setValue,
  onSubmit,
  onTakeABreath,
}) {
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);
  useEffect(() => {
  const textarea = textareaRef.current;

  if (!textarea) return;

  textarea.style.height = "46px";

  if (!value.trim()) {
    textarea.style.overflowY = "hidden";
    return;
  }

  const maxHeight = 128;

  textarea.style.height = `${Math.min(
    textarea.scrollHeight,
    maxHeight
  )}px`;

  textarea.style.overflowY =
    textarea.scrollHeight > maxHeight
      ? "auto"
      : "hidden";
}, [value]);

  const [listening, setListening] = useState(false);

  function toggleMicrophone() {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Voice input is not supported in this browser. Please use Google Chrome or Microsoft Edge."
      );
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = (event) => {
      let transcript = "";

      for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
      ) {
        transcript += event.results[i][0].transcript;
      }

      setValue(transcript);

      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);

      setListening(false);

      if (event.error === "not-allowed") {
        alert(
          "Microphone permission was denied. Please allow microphone access for localhost."
        );
      } else if (event.error !== "no-speech") {
        alert(`Voice input error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (error) {
      console.error(
        "Could not start speech recognition:",
        error
      );

      setListening(false);
      recognitionRef.current = null;
    }
  }

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  function submit(e) {
    e.preventDefault();
    onSubmit();
  }

  function useSuggestion(text) {
  setValue(text);

  requestAnimationFrame(() => {
    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.focus();

    const end = textarea.value.length;

    textarea.setSelectionRange(end, end);
  });
}

  return (
    <section className="relative flex h-full items-start justify-center overflow-hidden px-6 pt-[14vh]">
      <LandingBackground />

      <div className="relative w-full max-w-[760px] text-center">
        <div className="mb-5 text-[11px] font-semibold uppercase tracking-[0.18em] text-wa-accent">
          Wellness AI
        </div>

        <h1 className="m-0 text-[clamp(38px,4.5vw,54px)] font-semibold leading-[1.08] tracking-[-0.045em] text-wa-text">
          Whenever you're ready.
        </h1>

        <p className="mx-auto mt-5 max-w-[540px] text-[16px] leading-7 text-wa-muted">
          Take your time — there's no wrong way to ask.
        </p>

        <form
          onSubmit={submit}
          className={`mx-auto mt-9 flex min-h-[62px] items-end rounded-wa border bg-wa-surface/90 p-2 shadow-[0_8px_28px_rgba(72,100,72,0.06)] backdrop-blur-sm transition-all duration-200 ${
            listening
              ? "border-wa-accent/70"
              : "border-wa-border focus-within:border-wa-accent/50"
          }`}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit(e);
              }
            }}
            placeholder={
              listening
                ? "Listening..."
                : "What would you like to know?"
            }
            aria-label="What would you like to know?"
            className="min-h-[46px] max-h-32 flex-1 resize-none overflow-y-auto border-0 bg-transparent px-4 py-3 text-[15px] leading-6 text-wa-text outline-none ring-0 placeholder:text-wa-muted focus:border-0 focus:outline-none focus:ring-0"
          />

          <div className="mb-0.5 flex shrink-0 items-center gap-1">
            {/* Take a Breath */}
            <button
              type="button"
              onClick={onTakeABreath}
              title="Take a Breath"
              aria-label="Take a Breath"
              className="flex h-10 w-10 items-center justify-center rounded-full text-wa-muted transition hover:bg-wa-accent/10 hover:text-wa-accent"
            >
              <BreathIcon size={20} strokeWidth={1.8} />
            </button>

            {/* Microphone */}
            <button
              type="button"
              onClick={toggleMicrophone}
              title={listening ? "Stop listening" : "Voice input"}
              aria-label={
                listening ? "Stop listening" : "Voice input"
              }
              className={`flex h-10 w-10 items-center justify-center rounded-full transition ${
                listening
                  ? "bg-wa-accent/15 text-wa-accent"
                  : "text-wa-muted hover:bg-wa-accent/10 hover:text-wa-accent"
              }`}
            >
              <Mic size={18} strokeWidth={1.8} />
            </button>

            {/* Send */}
            <button
              type="submit"
              disabled={!value.trim()}
              title="Send message"
              aria-label="Send message"
              className="flex h-10 w-10 items-center justify-center rounded-wa-sm bg-wa-sidebar text-wa-muted transition hover:bg-wa-accentSoft/40 hover:text-wa-text disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowUp size={18} strokeWidth={1.8} />
            </button>
          </div>
        </form>

        <div className="mt-6 flex justify-center gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => useSuggestion(suggestion)}
              className="rounded-full border border-wa-border px-5 py-2 text-[13px] text-wa-muted transition hover:border-wa-accent/40 hover:bg-wa-accentSoft/30 hover:text-wa-text"
            >
              {suggestion}
            </button>
          ))}
        </div>

        <p className="mt-7 text-[12px] text-wa-muted">
          {listening
            ? "Listening · Speak clearly"
            : "General wellbeing information for exploration and support."}
        </p>
      </div>
    </section>
  );
}