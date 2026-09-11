import { ArrowUp, Mic } from "lucide-react";
import BreathIcon from "./icons/BreathIcon";
import { useEffect, useRef, useState } from "react";

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  onTakeABreath,
  disabled = false,
}) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (value.trim() && !disabled) {
        onSubmit();
      }
    }
  };

  useEffect(() => {
  const textarea = textareaRef.current;

  if (!textarea) return;

  textarea.style.height = "auto";

  const maxHeight = 128;
  textarea.style.height = `${Math.min(
    textarea.scrollHeight,
    maxHeight
  )}px`;
}, [value]);

  function toggleMicrophone() {
  if (disabled) return;

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

    onChange(transcript);
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);

    setListening(false);

    if (event.error === "not-allowed") {
      alert(
        "Microphone permission was denied. Please allow microphone access for localhost."
      );
    } else if (event.error === "no-speech") {
      // No speech detected — don't show an error.
    } else {
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
    console.error("Could not start speech recognition:", error);
    setListening(false);
    recognitionRef.current = null;
  }
}

  return (
    <div className="border-t border-wa-border bg-wa-sidebar/90 px-4 py-5 backdrop-blur">
      <div className="mx-auto max-w-3xl">
        <div
          className={`flex items-end gap-3 rounded-wa border bg-wa-surface px-4 py-3 shadow-[0_4px_20px_rgba(72,90,80,0.06)] transition focus-within:shadow-md ${
            listening
              ? "border-wa-accent/70"
              : "border-wa-border focus-within:border-wa-accent/50"
          }`}
        >
          {/* Message input */}
          <textarea
  ref={textareaRef}
  value={value}
  onChange={(event) => onChange(event.target.value)}
  onKeyDown={handleKeyDown}
  disabled={disabled}
  rows={1}
            placeholder={
              listening
                ? "Listening..."
                : "What would you like to know?"
            }
            className="min-h-[40px] max-h-32 flex-1 resize-none overflow-y-auto bg-transparent py-2 text-[15px] leading-6 text-wa-text outline-none placeholder:text-wa-muted/80 disabled:cursor-not-allowed"
            aria-label="Message"
          />

          <div className="flex shrink-0 items-center gap-1">

            {/* Take a Breath */}
<button
  type="button"
  onClick={onTakeABreath}
  disabled={disabled}
  title="Take a Breath"
  aria-label="Take a Breath"
  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-wa-muted transition hover:bg-wa-accent/10 hover:text-wa-accent disabled:cursor-not-allowed disabled:opacity-40"
>
  <BreathIcon size={20} strokeWidth={1.8} />
</button>

            {/* Microphone */}
            <button
              type="button"
              onClick={toggleMicrophone}
              disabled={disabled}
              title="Voice input"
              aria-label="Voice input"
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition ${
                listening
                  ? "bg-wa-accent/15 text-wa-accent"
                  : "text-wa-muted hover:bg-wa-accent/10 hover:text-wa-accent"
              }`}
            >
              <Mic size={18} strokeWidth={1.8} />
            </button>

            {/* Send */}
            <button
              type="button"
              onClick={onSubmit}
              disabled={!value.trim() || disabled}
              title="Send message"
              aria-label="Send message"
              className="flex h-10 w-10 items-center justify-center rounded-wa-sm bg-wa-sidebar text-wa-muted transition hover:bg-wa-accentSoft/40 hover:text-wa-text disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowUp size={18} strokeWidth={1.8} />
            </button>
          </div>
        </div>

        <p className="mt-2 text-center text-[11px] text-wa-muted">
          {listening
            ? "Listening · Speak clearly"
            : "Enter to send · Shift + Enter for a new line"}
        </p>
      </div>
    </div>
  );
}