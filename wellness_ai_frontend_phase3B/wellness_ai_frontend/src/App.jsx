import { useEffect, useMemo, useRef, useState } from "react";
import Sidebar from "./components/Sidebar";
import EmptyState from "./components/EmptyState";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import BreathingGuide from "./components/BreathingGuide";
import { sendChatMessage } from "./api";

const initialChats = [];

function generateChatTitle(text) {
  const cleaned = text
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[?.!,]+$/, "");
  
  const MAX_TITLE_LENGTH = 34;

  const lower = cleaned.toLowerCase();

  // Common wellness topics
  if (lower.includes("panic attack") || lower.includes("panic attacks")) {
    return "Panic attacks";
  }

  if (
    lower.includes("stress") &&
    (lower.includes("manage") ||
      lower.includes("management") ||
      lower.includes("cope"))
  ) {
    return "Managing stress";
  }

  if (
    lower.includes("sleep") ||
    lower.includes("insomnia") ||
    lower.includes("sleeping")
  ) {
    return "Sleep";
  }

  if (
    lower.includes("breathing") ||
    lower.includes("breath exercise") ||
    lower.includes("breathing exercise")
  ) {
    return "Breathing exercises";
  }

  if (
    lower.includes("anxiety") ||
    lower.includes("anxious")
  ) {
    return "Anxiety";
  }

  if (
    lower.includes("eating disorder") ||
    lower.includes("eating disorders")
  ) {
    return "Eating disorders";
  }

  if (
    lower.includes("depression") ||
    lower.includes("depressed")
  ) {
    return "Depression";
  }

    // Keep natural "How can I..." questions as titles.
  if (/^how can\b/i.test(cleaned)) {
    return cleaned.length > 34
      ? `${cleaned.slice(0, 34)}…`
      : cleaned;
  }

  // Remove common question openings
  const withoutQuestionStart = cleaned
    .replace(
      /^(what|why|how|when|where|can you|could you|would you|tell me about|explain|please explain|please tell me about)\s+/i,
      ""
    )
    .replace(
      /^(are|is|do|does|can|could|should|would)\s+/i,
      ""
    );

  const words = withoutQuestionStart
    .split(" ")
    .filter(Boolean)
    .slice(0, 5);

  if (words.length === 0) {
    return "New conversation";
  }

  const title = words.join(" ");

  const finalTitle =
    title.length > MAX_TITLE_LENGTH
      ? `${title.slice(0, MAX_TITLE_LENGTH)}…`
      : title;

  return finalTitle.charAt(0).toUpperCase() + finalTitle.slice(1);
}

function getConversationHistory(messages) {
  if (!Array.isArray(messages)) {
    return [];
  }

  return messages;
}

function getChatErrorMessage(error) {
  if (error?.status === 400 && error?.message) {
    return error.message;
  }

  return "I’m having trouble connecting right now. Please try again in a moment.";
}

export default function App() {
  const [chats, setChats] = useState(() => {
    try {
      const savedChats = sessionStorage.getItem("wellness_ai_chats");

      return savedChats
        ? JSON.parse(savedChats)
        : initialChats;
    } catch (error) {
      console.error("Could not restore conversations:", error);
      return initialChats;
    }
  });
  const [activeChat, setActiveChat] = useState(() => {
  try {
    const savedActiveChat = sessionStorage.getItem(
      "wellness_ai_active_chat"
    );

    return savedActiveChat
      ? Number(savedActiveChat)
      : null;
  } catch (error) {
    console.error(
      "Could not restore active conversation:",
      error
    );
    return null;
  }
});
  const [draft, setDraft] = useState("");
  const [loadingChats, setLoadingChats] = useState({});
  const [retryingMessage, setRetryingMessage] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [editingMessage, setEditingMessage] = useState(null);
  const [editDraft, setEditDraft] = useState("");
  const [showConversationDetails, setShowConversationDetails] = useState(false);
  const [showAboutAssistant, setShowAboutAssistant] = useState(false);
  const [showBreathingGuide, setShowBreathingGuide] = useState(false);

  const messagesEndRef = useRef(null);

  const currentChat = useMemo(
    () => chats.find((chat) => chat.id === activeChat),
    [chats, activeChat]
  );

  // Automatically scroll to the newest message.
  useEffect(() => {
    if (!currentChat) return;

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [currentChat?.messages.length]);
   
  useEffect(() => {
  try {
    sessionStorage.setItem(
      "wellness_ai_chats",
      JSON.stringify(chats)
    );
  } catch (error) {
    console.error("Could not save conversations:", error);
  }
}, [chats]);
useEffect(() => {
  try {
    if (activeChat === null) {
      sessionStorage.removeItem("wellness_ai_active_chat");
    } else {
      sessionStorage.setItem(
        "wellness_ai_active_chat",
        String(activeChat)
      );
    }
  } catch (error) {
    console.error(
      "Could not save active conversation:",
      error
    );
  }
}, [activeChat]);

  function newChat() {
    setActiveChat(null);
    setDraft("");
  }

  function selectChat(id) {
    setActiveChat(id);
    setDraft("");
  }
  
  function setChatLoading(chatId, isLoading) {
  setLoadingChats((prev) => {
    const currentCount = prev[chatId] || 0;

    const nextCount = isLoading
      ? currentCount + 1
      : Math.max(0, currentCount - 1);

    const next = { ...prev };

    if (nextCount === 0) {
      delete next[chatId];
    } else {
      next[chatId] = nextCount;
    }

    return next;
  });
}

  
async function sendMessage() {
  // When editing, use the inline edit value.
  // Otherwise use the normal composer value.
  const text =
    editingMessage !== null
      ? editDraft.trim()
      : draft.trim();

    if (!text) {
  return;
}

// -----------------------------
// EDIT MODE
// -----------------------------
if (editingMessage !== null && activeChat !== null) {
  const chat = chats.find(
    (item) => item.id === activeChat
  );

  if (!chat) return;

  const text = editDraft.trim();

  if (!text) return;

  const editIndex = editingMessage;

  const historyBeforeEdit = getConversationHistory(
  chat.messages.slice(0, editIndex)
);

  // Exit inline editing immediately.
  setEditingMessage(null);
  setEditDraft("");

  // Immediately replace the old question.
  // The old answer disappears at the same time.
  setChats((prev) =>
    prev.map((item) => {
      if (item.id !== activeChat) {
        return item;
      }

     const updatedTitle =
  editIndex === 0 && !item.titleManuallySet
    ? text.length > 34
      ? `${text.slice(0, 34)}…`
      : text
    : item.title;

return {
  ...item,
  title: updatedTitle,
  messages: [
    ...item.messages.slice(0, editIndex),
    {
      role: "user",
      content: text,
    },
  ],
};
    })
  );

  // Show one global Thinking indicator.
  setChatLoading(activeChat, true);

  try {
    const result = await sendChatMessage(
      text,
      historyBeforeEdit
    );

    setChats((prev) =>
      prev.map((item) => {
        if (item.id !== activeChat) {
          return item;
        }

      const updatedTitle =
  editIndex === 0 && !item.titleManuallySet
    ? text.length > 34
      ? `${text.slice(0, 34)}…`
      : text
    : item.title;

return {
  ...item,
  title: updatedTitle,
  messages: [
    ...item.messages.slice(0, editIndex),
    {
      role: "user",
      content: text,
    },
    {
      role: "assistant",
      content: result.answer,
    },
  ],
};
      })
    );
  } catch (error) {
    console.error(
      "Edit request failed:",
      error
    );

    setChats((prev) =>
      prev.map((item) => {
        if (item.id !== activeChat) {
          return item;
        }

        return {
          ...item,
          messages: [
            ...item.messages.slice(0, editIndex),
            {
              role: "user",
              content: text,
            },
            {
  role: "assistant",
 content: getChatErrorMessage(error),
  retryText: text,
},
          ],
        };
      })
    );
  } finally {
    setChatLoading(activeChat, false);
  }

  return;
}

  // -----------------------------
  // NORMAL MESSAGE
  // -----------------------------

  setDraft("");

    // --------------------------------
  // Existing conversation
  // --------------------------------
  if (activeChat !== null) {
    const chat = chats.find(
      (item) => item.id === activeChat
    );

    if (!chat) {
      return;
    }
    
    setChatLoading(activeChat, true);

    const history = getConversationHistory(chat.messages);

    // Show user's message IMMEDIATELY.
    setChats((prev) =>
      prev.map((item) =>
        item.id === activeChat
          ? {
              ...item,
              messages: [
                ...item.messages,
                {
                  role: "user",
                  content: text,
                },
              ],
            }
          : item
      )
    );

    try {
      const result = await sendChatMessage(
        text,
        history
      );

      // Add the AI answer after backend responds.
      setChats((prev) =>
        prev.map((item) =>
          item.id === activeChat
            ? {
                ...item,
                messages: [
                  ...item.messages,
                  {
                    role: "assistant",
                    content: result.answer,
                  },
                ],
              }
            : item
        )
      );
    } catch (error) {
      console.error(
        "Chat request failed:",
        error
      );

      setChats((prev) =>
        prev.map((item) =>
          item.id === activeChat
            ? {
                ...item,
                messages: [
                  ...item.messages,
                  {
                    role: "assistant",
                    content: getChatErrorMessage(error),
                    retryText: text,
                  },
                ],
              }
            : item
        )
      );
    } finally {
      setChatLoading(activeChat, false);
    }

    return;
  }
   
  // --------------------------------
  // New conversation
  // --------------------------------

  const id = Date.now();

  const title = generateChatTitle(text);

  // Create the conversation immediately
  // with the user's question.
  const newConversation = {
  id,
  title,
  titleManuallySet: false,
  messages: [
    {
      role: "user",
      content: text,
    },
  ],
};

  setChats((prev) => [
    newConversation,
    ...prev,
  ]);

  setActiveChat(id);
  setChatLoading(id, true);

  try {
    const result = await sendChatMessage(
      text,
      []
    );

    setChats((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              messages: [
                ...item.messages,
                {
                  role: "assistant",
                  content: result.answer,
                },
              ],
            }
          : item
      )
    );
  } catch (error) {
    console.error(
      "Chat request failed:",
      error
    );

    setChats((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              messages: [
                ...item.messages,
                {
  role: "assistant",
  content: getChatErrorMessage(error),
  retryText: text,
},
              ],
            }
          : item
      )
    );
  } finally {
    setChatLoading(id, false);
  }
}

  function renameChat(chat, newTitle) {
  const title = newTitle.trim();

  if (!title) return;

  setChats((prev) =>
    prev.map((item) =>
      item.id === chat.id
        ? {
            ...item,
            title,
            titleManuallySet: true,
          }
        : item
    )
  );
}

  function deleteChat(chat) {
    setDeleteTarget(chat);
  }
  
  function togglePinChat(chat) {
  setChats((prev) =>
    prev.map((item) =>
      item.id === chat.id
        ? {
            ...item,
            pinned: !item.pinned,
          }
        : item
    )
  );
}
  function toggleArchiveChat(chat) {
  const willArchive = !chat.archived;

  setChats((prev) =>
    prev.map((item) =>
      item.id === chat.id
        ? {
            ...item,
            archived: willArchive,
          }
        : item
    )
  );

  if (willArchive && activeChat === chat.id) {
    setActiveChat(null);
  }
}

  function confirmDelete() {
    if (!deleteTarget) return;

    setChats((prev) =>
      prev.filter((item) => item.id !== deleteTarget.id)
    );

    if (activeChat === deleteTarget.id) {
      setActiveChat(null);
    }

    setDeleteTarget(null);
  }

  function cancelDelete() {
    setDeleteTarget(null);
  }
  
  function editMessage(messageIndex) {
  if (!currentChat) return;

  const message = currentChat.messages[messageIndex];

  if (!message || message.role !== "user") return;

  setEditDraft(message.content);
  setEditingMessage(messageIndex);
}

function cancelEdit() {
  setEditingMessage(null);
  setEditDraft("");
}

    async function retryMessage(chatId, messageIndex) {
  if (loadingChats[chatId]) return;

    const chat = chats.find(
      (item) => item.id === chatId
    );

    if (!chat) return;

    const failedMessage = chat.messages[messageIndex];

    if (
      !failedMessage ||
      failedMessage.role !== "assistant" ||
      !failedMessage.retryText
    ) {
      return;
    }

    const retryText = failedMessage.retryText;

    // The user message is immediately before the failed AI response.
    const userMessageIndex = messageIndex - 1;

    // Use the conversation history BEFORE the user message
    // that originally failed.
    const history = getConversationHistory(
  chat.messages.slice(0, userMessageIndex)
);

    // Remember exactly which failed message is being retried.
    setRetryingMessage({
      chatId,
      messageIndex,
    });

    setChatLoading(chatId, true);

    try {
      const result = await sendChatMessage(
        retryText,
        history
      );

      // Replace the failed AI response with the successful answer.
      setChats((prev) =>
        prev.map((item) =>
          item.id === chatId
            ? {
                ...item,
                messages: item.messages.map(
                  (message, index) =>
                    index === messageIndex
                      ? {
                          role: "assistant",
                          content: result.answer,
                        }
                      : message
                ),
              }
            : item
        )
      );
    } catch (error) {
      console.error(
        "Retry request failed:",
        error
      );

      // Keep the error message so it can be retried again.
      setChats((prev) =>
        prev.map((item) =>
          item.id === chatId
            ? {
                ...item,
                messages: item.messages.map(
                  (message, index) =>
                    index === messageIndex
                      ? {
                          role: "assistant",
                          content: getChatErrorMessage(error),
                          retryText,
                        }
                      : message
                ),
              }
            : item
        )
      );
    } finally {
      setRetryingMessage(null);
      setChatLoading(chatId, false);
    }
  } 
   
   return (
    <div className="h-screen overflow-hidden bg-wellness-bg text-wellness-text">
      <div className="flex h-full">
        
        {/* Sidebar */}
{!showBreathingGuide && (
  <Sidebar
    chats={chats}
    activeChat={activeChat}
    onNewChat={newChat}
    onSelectChat={selectChat}
    onRename={renameChat}
    onDelete={deleteChat}
    onPin={togglePinChat}
    onArchive={toggleArchiveChat}
    onConversationDetails={() => setShowConversationDetails(true)}
    onAboutAssistant={() => setShowAboutAssistant(true)}
    onTakeABreath={() => setShowBreathingGuide(true)}
  />
)}

        {/* Main application area */}
        <main className="relative min-w-0 flex-1 overflow-hidden bg-[#F5F3EE]">
          {/* Soft background atmosphere */}
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_28%,rgba(211,228,217,0.65),transparent_46%)]" />

          <div className="relative h-full">
            {showBreathingGuide ? (
  <BreathingGuide
    onBack={() => setShowBreathingGuide(false)}
  />
) : !currentChat ? (
  <EmptyState
    value={draft}
    setValue={setDraft}
    onSubmit={sendMessage}
    onTakeABreath={() => setShowBreathingGuide(true)}
  />
) : (
  <div className="flex h-full flex-col">
                {/* Scrollable conversation area */}
                <div className="min-h-0 flex-1 overflow-y-auto">
                  {/* Content remains centered, scrollbar stays at far right */}
                  <div className="mx-auto max-w-[1000px] px-6 pb-8 pt-16">
                    {/* Conversation heading */}
                    <div className="mb-10 border-b border-wellness-border pb-5">
                      <div className="text-[12px] font-semibold uppercase tracking-[0.08em] text-wellness-accent">
                        Wellness AI
                      </div>

                      <h1 className="mt-2 break-words text-xl font-semibold tracking-[-0.02em]">
                        {currentChat.title}
                      </h1>
                    </div>

                   {/* Messages */}
{currentChat.messages.map((message, index) => {
  const isBeingRetried =
    retryingMessage?.chatId === currentChat.id &&
    retryingMessage?.messageIndex === index;

  // Retry:
  // hide the old failed response and show Thinking
  // exactly where that response was.
  if (isBeingRetried) {
    return (
      <div
        key={`${currentChat.id}-retry-${index}`}
        className="mb-10 text-left"
      >
        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
          Wellness AI
        </div>

        <div className="mt-3 flex items-center text-[14px] text-wa-muted">
          <span>Thinking</span>

          <span
            className="thinking-dots ml-1"
            aria-hidden="true"
          >
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </div>
      </div>
    );
  }

  return (
    <ChatMessage
      key={`${currentChat.id}-${index}`}
      role={message.role}
      content={message.content}
      retryText={message.retryText}
      onRetry={
        message.role === "assistant" && message.retryText
          ? () => retryMessage(currentChat.id, index)
          : undefined
      }
      retrying={
        retryingMessage?.chatId === currentChat.id &&
        retryingMessage?.messageIndex === index
      }
      onEdit={
        message.role === "user"
          ? () => editMessage(index)
          : undefined
      }
      editing={
        message.role === "user" &&
        editingMessage === index
      }
      editValue={
        message.role === "user" &&
        editingMessage === index
          ? editDraft
          : ""
      }
      onEditChange={setEditDraft}
      onEditSubmit={sendMessage}
      onEditCancel={cancelEdit}
    />
  );
})}

{/* Normal request Thinking */}
{loadingChats[currentChat.id] &&
  !(
    retryingMessage?.chatId === currentChat.id
  ) && (
    <div className="mb-10 text-left">
      <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
        Wellness AI
      </div>

      <div className="mt-3 flex items-center text-[14px] text-wa-muted">
        <span>Thinking</span>

        <span
          className="thinking-dots ml-1"
          aria-hidden="true"
        >
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </span>
      </div>
    </div>
  )}
                        

                    {/* Auto-scroll target */}
                    <div ref={messagesEndRef} />
                  </div>
                </div>

                {/* Input */}
                <ChatInput
                  value={draft}
                  onChange={setDraft}
                  onSubmit={sendMessage}
                  onTakeABreath={() => setShowBreathingGuide(true)}
                  disabled={!!loadingChats[currentChat.id]}
                />
              </div>
            )}
          </div>
        </main>

        {/* Conversation Details */}
{showConversationDetails && (
  <div
    className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 px-6 backdrop-blur-[2px]"
    onClick={() => setShowConversationDetails(false)}
  >
    <div
      className="w-full max-w-[420px] rounded-wa border border-wa-border bg-wa-surface p-6 shadow-[0_20px_60px_rgba(50,65,50,0.15)]"
      onClick={(event) => event.stopPropagation()}
    >
      <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
        Conversation
      </div>

      <h2 className="mt-3 text-xl font-semibold tracking-[-0.02em] text-wa-text">
        Conversation details
      </h2>

      {currentChat ? (
        <div className="mt-5 space-y-4 text-sm">
          <div>
            <div className="text-xs text-wa-muted">
              Title
            </div>
            <div className="mt-1 text-wa-text">
              {currentChat.title}
            </div>
          </div>

          <div>
            <div className="text-xs text-wa-muted">
              Messages
            </div>
            <div className="mt-1 text-wa-text">
              {currentChat.messages.length}
            </div>
          </div>

          <div>
            <div className="text-xs text-wa-muted">
              Status
            </div>
            <div className="mt-1 text-wa-text">
              {currentChat.archived
                ? "Archived"
                : "Active"}
            </div>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-wa-muted">
          Select a conversation to view its details.
        </p>
      )}

      <div className="mt-6 flex justify-end">
        <button
          type="button"
          onClick={() => setShowConversationDetails(false)}
          className="rounded-wa border border-wa-border bg-wa-surface px-4 py-2.5 text-sm font-medium text-wa-text transition hover:bg-wa-sidebar"
        >
          Close
        </button>
      </div>
    </div>
  </div>
)}

        {/* About Assistant */}
{showAboutAssistant && (
  <div
    className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 px-6 backdrop-blur-[2px]"
    onClick={() => setShowAboutAssistant(false)}
  >
    <div
      className="w-full max-w-[420px] rounded-wa border border-wa-border bg-wa-surface p-6 shadow-[0_20px_60px_rgba(50,65,50,0.15)]"
      onClick={(event) => event.stopPropagation()}
    >
      <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
        Wellness AI
      </div>

      <h2 className="mt-3 text-xl font-semibold tracking-[-0.02em] text-wa-text">
        About this assistant
      </h2>

      <p className="mt-4 text-[14px] leading-6 text-wa-muted">
        Wellness AI is a calm space for exploring wellbeing
        information. It provides information grounded in the
        wellness knowledge available to the assistant.
      </p>

      <p className="mt-3 text-[14px] leading-6 text-wa-muted">
        It is designed to provide supportive information and
        general guidance, not to replace professional care.
      </p>

      <div className="mt-6 flex justify-end">
        <button
          type="button"
          onClick={() => setShowAboutAssistant(false)}
          className="rounded-wa border border-wa-border bg-wa-surface px-4 py-2.5 text-sm font-medium text-wa-text transition hover:bg-wa-sidebar"
        >
          Close
        </button>
      </div>
    </div>
  </div>
)}
       
        {/* Delete confirmation modal */}
        {deleteTarget && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 px-6 backdrop-blur-[2px]"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
          >
            <div className="w-full max-w-[420px] rounded-wa border border-wa-border bg-wa-surface p-6 shadow-[0_20px_60px_rgba(50,65,50,0.15)]">
              <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-wa-accent">
                Wellness AI
              </div>

              <h2
                id="delete-dialog-title"
                className="mt-3 text-xl font-semibold tracking-[-0.02em] text-wa-text"
              >
                Delete conversation?
              </h2>

              <p className="mt-3 text-[14px] leading-6 text-wa-muted">
                This conversation will be removed from your
                current session. This action cannot be undone.
              </p>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={cancelDelete}
                  className="rounded-wa border border-wa-border bg-wa-surface px-4 py-2.5 text-sm font-medium text-wa-text transition hover:bg-wa-sidebar"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={confirmDelete}
                  className="rounded-wa bg-wa-sidebar px-4 py-2.5 text-sm font-medium text-wa-text transition hover:bg-wa-accentSoft/40"
                >
                  Delete conversation
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}