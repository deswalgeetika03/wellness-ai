import { useState } from "react";
import {
  Check,
  Copy,
  Pencil,
  RotateCcw,
} from "lucide-react";

export default function ChatMessage({
  role,
  content,
  onEdit,
  onRetry,
  retryText,
  retrying = false,
  editing = false,
  editValue = "",
  onEditChange,
  onEditSubmit,
  onEditCancel,
}) {
  const [copied, setCopied] = useState(false);

  async function copyMessage() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch (error) {
      console.error("Copy failed:", error);
    }
  }

  const isUser = role === "user";
  

  // ---------------------------------------------------------
  // INLINE EDIT MODE
  // ---------------------------------------------------------
  if (isUser && editing) {
    function handleEditKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        onEditCancel?.();
        return;
      }

      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();

        if (editValue.trim()) {
          onEditSubmit?.();
        }
      }
    }

    return (
      <div className="mb-8 flex flex-col items-end">
        <div className="w-full max-w-[72%]">
          <div className="mb-3 text-right text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
            You
          </div>

          <div className="rounded-wa border border-wa-border bg-wa-surface p-3 shadow-[0_4px_20px_rgba(72,90,80,0.06)]">
            <textarea
              autoFocus
  ref={(element) => {
    if (element) {
      element.focus();
      element.setSelectionRange(
        element.value.length,
        element.value.length
      );
    }
  }}
              value={editValue}
              onChange={(event) =>
                onEditChange?.(event.target.value)
              }
              onKeyDown={handleEditKeyDown}
              rows={2}
              className="max-h-40 min-h-[52px] w-full resize-none bg-transparent px-1 py-1 text-[15px] leading-7 text-wa-text outline-none"
              aria-label="Edit message"
            />

            <div className="mt-2 flex items-center justify-end gap-2 border-t border-wa-border pt-2">
              <button
                type="button"
                onClick={onEditCancel}
                className="rounded-wa px-3 py-2 text-[13px] text-wa-muted transition hover:bg-wa-sidebar hover:text-wa-text"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={onEditSubmit}
                disabled={!editValue.trim()}
                className="rounded-wa bg-wa-accent px-4 py-2 text-[13px] font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={
        isUser
          ? "mb-8 flex flex-col items-end"
          : "mb-10"
      }
    >
      {/* User message */}
      {isUser ? (
        <>
          <div className="max-w-[72%] text-right">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
              You
            </div>

            <p className="m-0 whitespace-pre-wrap [overflow-wrap:anywhere] text-[15px] leading-7 text-wa-text">
              {content}
            </p>
          </div>

          {/* User actions */}
          <div className="mt-3 flex items-center gap-1">
            

            <button
              type="button"
              onClick={copyMessage}
              title={copied ? "Copied" : "Copy"}
              aria-label={copied ? "Copied" : "Copy"}
              className="flex h-8 w-8 items-center justify-center rounded-wa-sm text-wa-muted transition hover:bg-wa-sidebar hover:text-wa-text"
            >
              {copied ? (
                <Check size={16} strokeWidth={1.8} />
              ) : (
                <Copy size={16} strokeWidth={1.8} />
              )}
            </button>

            {onEdit && (
              <button
                type="button"
                onClick={onEdit}
                title="Edit"
                aria-label="Edit message"
                className="flex h-8 w-8 items-center justify-center rounded-wa-sm text-wa-muted transition hover:bg-wa-sidebar hover:text-wa-text"
              >
                <Pencil
                  size={16}
                  strokeWidth={1.8}
                />
              </button>
            )}

            
          
          </div>
        </>
           ) : (
        /* Assistant message */
        <div>
  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
    Wellness AI
  </div>

  <p className="mt-4 whitespace-pre-wrap [overflow-wrap:anywhere] text-[15px] leading-7 text-wa-text">
  {content}
</p>

          <div className="mt-4 flex items-center gap-2">
            <button
              type="button"
              onClick={copyMessage}
              title={copied ? "Copied" : "Copy"}
              aria-label={copied ? "Copied" : "Copy"}
             className="flex h-8 w-8 items-center justify-center rounded-wa-sm text-wa-muted transition hover:bg-wa-accentSoft/50 hover:text-wa-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {copied ? (
                <Check size={16} strokeWidth={1.8} />
              ) : (
                <Copy size={16} strokeWidth={1.8} />
              )}
            </button>

            {onRetry && (
  <button
    type="button"
    onClick={onRetry}
    disabled={retrying}
    title={retrying ? "Trying again" : "Try again"}
    aria-label={retrying ? "Trying again" : "Try again"}
    className="flex h-8 w-8 items-center justify-center rounded-wa-sm text-wa-muted transition hover:bg-wa-accentSoft/50 hover:text-wa-accent disabled:cursor-not-allowed disabled:opacity-50"
  >
    <RotateCcw
      size={16}
      strokeWidth={1.8}
      className={retrying ? "animate-spin" : ""}
    />
  </button>
)}
          </div>
        </div>
      )}
    </div>
  );
}