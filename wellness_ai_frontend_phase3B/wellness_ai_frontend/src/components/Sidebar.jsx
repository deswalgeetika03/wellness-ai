import {
  Plus,
  Settings2,
  MoreHorizontal,
  Pencil,
  Pin,
  Archive,
  Trash2,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";

export default function Sidebar({
  chats,
  activeChat,
  onNewChat,
  onSelectChat,
  onRename,
  onDelete,
  onPin,
  onArchive,
  onConversationDetails,
  onAboutAssistant,
  onTakeABreath,
}) {
  const [openMenu, setOpenMenu] = useState(null);
  const [menuPosition, setMenuPosition] = useState(null);
  const [editingChat, setEditingChat] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const menuRef = useRef(null);

  const [sidebarWidth, setSidebarWidth] = useState(() => {
  const savedWidth = localStorage.getItem("wellness-sidebar-width");

  if (savedWidth) {
    const parsedWidth = Number(savedWidth);

    if (
      Number.isFinite(parsedWidth) &&
      parsedWidth >= 220 &&
      parsedWidth <= window.innerWidth * 0.5
    ) {
      return parsedWidth;
    }
  }

  return 270;
});
  const isResizing = useRef(false);
  
  const sortedChats = useMemo(() => {
  return [...chats].sort(
    (a, b) => Number(Boolean(b.pinned)) - Number(Boolean(a.pinned))
  );
}, [chats]);
function startResize(event) {
  event.preventDefault();

  isResizing.current = true;

  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";

  function handleMouseMove(moveEvent) {
    if (!isResizing.current) return;

    const newWidth = moveEvent.clientX;

    const minWidth = 220;
    const maxWidth = window.innerWidth * 0.5;

    const clampedWidth = Math.min(
      Math.max(newWidth, minWidth),
      maxWidth
    );

    setSidebarWidth(clampedWidth);
localStorage.setItem(
  "wellness-sidebar-width",
  String(clampedWidth)
);
  }

  function stopResize() {
    isResizing.current = false;

    document.body.style.cursor = "";
    document.body.style.userSelect = "";

    window.removeEventListener(
      "mousemove",
      handleMouseMove
    );

    window.removeEventListener(
      "mouseup",
      stopResize
    );
  }

  window.addEventListener(
    "mousemove",
    handleMouseMove
  );

  window.addEventListener(
    "mouseup",
    stopResize
  );
}

  function toggleMenu(chatId, event) {
  event.stopPropagation();

  if (openMenu === chatId) {
    setOpenMenu(null);
    setMenuPosition(null);
    return;
  }

  const row = event.currentTarget.closest(
    "[data-conversation]"
  );

  if (!row) return;

 const rect = row.getBoundingClientRect();

setMenuPosition({
  top: rect.top,
  left: rect.right + 8,
});

setOpenMenu(chatId);

requestAnimationFrame(() => {
  const menu = menuRef.current;

  if (!menu) return;

  const menuRect = menu.getBoundingClientRect();
  const bottomOverflow =
    menuRect.bottom - window.innerHeight;

  if (bottomOverflow > 0) {
    setMenuPosition((prev) => ({
      ...prev,
      top: Math.max(
        8,
        prev.top - bottomOverflow - 8
      ),
    }));
  }
});
}

  function handleAction(action, chat, event) {
    event.stopPropagation();
    setOpenMenu(null);
    setMenuPosition(null);

    if (action === "rename") {
      setEditingChat(chat.id);
      setEditingTitle(chat.title);
    }

    if (action === "pin") {
      onPin(chat);
    }

    if (action === "archive") {
      onArchive(chat);
    }

    if (action === "delete") {
      onDelete(chat);
    }
  }

  return (
    <aside
  className="relative flex h-full shrink-0 flex-col border-r border-wa-border bg-wa-sidebar"
  style={{ width: sidebarWidth }}
>
      {/* Header */}
<div className="px-5 pt-6">
  <div className="text-[20px] font-semibold tracking-[-0.02em] text-wa-text">
    Wellness AI
  </div>

  <p className="mt-2 max-w-[220px] text-[14px] leading-6 text-wa-muted">
    A calm space to explore wellbeing information.
  </p>
</div>

{/* Sidebar actions */}
<div className="px-5 pt-5">
  {/* Take a Breath */}
  

  {/* New conversation */}
  <button
    type="button"
    onClick={onNewChat}
    className="flex w-full items-center justify-center gap-3 rounded-wa border border-wa-border bg-wa-surface px-4 py-3 text-sm font-medium text-wa-text shadow-[0_4px_20px_rgba(72,90,80,0.06)] transition hover:bg-wa-accentSoft/30"
  >
    <Plus size={18} strokeWidth={1.8} />
    <span>New conversation</span>
  </button>
</div>
        

      {/* Conversations */}
<div className="flex min-h-0 flex-1 flex-col">
  {/* Fixed heading */}
  <div className="shrink-0 px-6 pb-3 pt-6">
    <div className="text-[12px] font-semibold uppercase tracking-[0.08em] text-wa-accent">
      Conversations
    </div>
  </div>

  {/* Only chat list scrolls */}
  <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6 sidebar-scroll">
    {/* Active conversations */}
    <div className="space-y-1.5">
      {sortedChats
        .filter((chat) => !chat.archived)
        .map((chat) => {
            const selected = chat.id === activeChat;
            const menuOpen = openMenu === chat.id;

            return (
              <div
               key={chat.id}
               data-conversation
               className={`group relative flex w-full items-center rounded-wa border transition ${
               selected
                ? "border-wa-border bg-wa-surface shadow-sm"
                : "border-transparent hover:border-wa-border hover:bg-wa-surface/70"
               }`}
              >
                {/* Conversation */}
                {editingChat === chat.id ? (
  <input
    autoFocus
    value={editingTitle}
    onChange={(event) => setEditingTitle(event.target.value)}
    onClick={(event) => event.stopPropagation()}
    onKeyDown={(event) => {
      if (event.key === "Enter") {
        event.preventDefault();

        const title = editingTitle.trim();

        if (!title) {
          setEditingTitle(chat.title);
          setEditingChat(null);
          return;
        }

        onRename(chat, title);
        setEditingChat(null);
      }

      if (event.key === "Escape") {
        event.preventDefault();
        setEditingChat(null);
        setEditingTitle("");
      }
    }}
    className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-[14px] text-wa-text outline-none"
  />
) : (
  <button
    onClick={() => {
  setOpenMenu(null);
  setEditingChat(null);
  setEditingTitle("");
  onSelectChat(chat.id);
}}
    title={chat.title}
    className="min-w-0 flex-1 px-3 py-2.5 text-left text-[14px] text-wa-text"
  >
    <span className="flex min-w-0 items-center gap-2">
      {chat.pinned && (
        <Pin
          size={13}
          strokeWidth={1.8}
          className="shrink-0 text-wa-accent"
        />
      )}

      <span className="block truncate">
        {chat.title}
      </span>
    </span>
  </button>
)}

                {/* Three-dot button */}
                <button
                  type="button"
                  onClick={(event) =>
                    toggleMenu(chat.id, event)
                  }
                  aria-label={`Conversation options for ${chat.title}`}
                  aria-expanded={menuOpen}
                  className={`mr-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-wa-sm text-wa-muted transition ${
                    menuOpen
                      ? "bg-wa-sidebar text-wa-text"
                      : "opacity-0 group-hover:opacity-100 hover:bg-wa-sidebar hover:text-wa-text"
                  }`}
                >
                  <MoreHorizontal
                    size={17}
                    strokeWidth={1.8}
                  />
                </button>

                {/* Context menu */}
                {menuOpen && menuPosition && (
                  <div
                  ref={menuRef}
                   className="fixed z-[100] w-[190px] rounded-[14px] border border-wa-border bg-wa-surface p-1.5 shadow-[0_14px_40px_rgba(50,65,50,0.16)]"
                   style={{
                    top: menuPosition.top,
                    left: menuPosition.left,
                   }}
                   onClick={(event) =>
                    event.stopPropagation()
                   }
                  >
                    {/* Rename */}
                    <button
                      type="button"
                      onClick={(event) =>
                        handleAction(
                          "rename",
                          chat,
                          event
                        )
                      }
                      className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-wa-text transition hover:bg-wa-sidebar"
                    >
                      <Pencil
                        size={16}
                        strokeWidth={1.8}
                      />
                      Rename
                    </button>

                    {/* Pin */}
                    <button
                      type="button"
                      onClick={(event) =>
                        handleAction(
                          "pin",
                          chat,
                          event
                        )
                      }
                      className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-wa-text transition hover:bg-wa-sidebar"
                    >
                      <Pin
                        size={16}
                        strokeWidth={1.8}
                      />
                      {chat.pinned
                        ? "Unpin chat"
                        : "Pin chat"}
                    </button>

                    {/* Archive */}
                    <button
                      type="button"
                      onClick={(event) =>
                        handleAction(
                          "archive",
                          chat,
                          event
                        )
                      }
                      className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-wa-text transition hover:bg-wa-sidebar"
                    >
                      <Archive
                        size={16}
                        strokeWidth={1.8}
                      />
                      {chat.archived
                        ? "Unarchive"
                        : "Archive"}
                    </button>

                    <div className="my-1.5 border-t border-wa-border" />

                    {/* Delete */}
                    <button
                      type="button"
                      onClick={(event) =>
                        handleAction(
                          "delete",
                          chat,
                          event
                        )
                      }
                      className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-[#8A5555] transition hover:bg-[#F5EAEA]"
                    >
                      <Trash2
                        size={16}
                        strokeWidth={1.8}
                      />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>

         </div>
      
              {/* Archived */}
        {chats.some((chat) => chat.archived) && (
          <div className="mt-10 pt-5">
            <button
              type="button"
              onClick={() => setShowArchived((prev) => !prev)}
              className="flex w-full items-center justify-between px-1 text-xs font-medium uppercase tracking-[0.08em] text-wa-muted transition hover:text-wa-text"
            >
              <span>Archived</span>

              <span className="text-[13px]">
                {showArchived ? "−" : "+"}
              </span>
            </button>

            {showArchived && (
              <div className="mt-3 space-y-1.5">
                {sortedChats
  .filter((chat) => chat.archived)
  .map((chat) => {
                    const selected = chat.id === activeChat;
                    const menuOpen = openMenu === chat.id;

                    return (
                      <div
                        key={chat.id}
                        data-conversation
                        className={`group relative flex w-full items-center rounded-wa border transition ${
                          selected
                            ? "border-wa-border bg-wa-surface shadow-sm"
                            : "border-transparent hover:border-wa-border hover:bg-wa-surface/70"
                        }`}
                      >
                        {/* Archived conversation */}
                        {editingChat === chat.id ? (
                          <input
                            autoFocus
                            value={editingTitle}
                            onChange={(event) =>
                              setEditingTitle(event.target.value)
                            }
                            onClick={(event) =>
                              event.stopPropagation()
                            }
                            onKeyDown={(event) => {
                              if (event.key === "Enter") {
                                event.preventDefault();

                                const title =
                                  editingTitle.trim();

                                if (!title) {
                                  setEditingChat(null);
                                  setEditingTitle("");
                                  return;
                                }

                                onRename(chat, title);
                                setEditingChat(null);
                                setEditingTitle("");
                              }

                              if (event.key === "Escape") {
                                event.preventDefault();
                                setEditingChat(null);
                                setEditingTitle("");
                              }
                            }}
                            className="min-w-0 flex-1 bg-transparent px-3 py-2.5 text-[14px] text-wa-text outline-none"
                          />
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
  setOpenMenu(null);
  setEditingChat(null);
  setEditingTitle("");
  onSelectChat(chat.id);
}}
                            title={chat.title}
                            className="min-w-0 flex-1 px-3 py-2.5 text-left text-[14px] text-wa-muted"
                          >
                            <span className="block truncate">
                              {chat.title}
                            </span>
                          </button>
                        )}

                        {/* Three-dot button */}
                        <button
                          type="button"
                          onClick={(event) =>
                            toggleMenu(chat.id, event)
                          }
                          aria-label={`Conversation options for ${chat.title}`}
                          aria-expanded={menuOpen}
                          className={`mr-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-wa-sm text-wa-muted transition ${
                            menuOpen
                              ? "bg-wa-sidebar text-wa-text"
                              : "opacity-0 group-hover:opacity-100 hover:bg-wa-sidebar hover:text-wa-text"
                          }`}
                        >
                          <MoreHorizontal
                            size={17}
                            strokeWidth={1.8}
                          />
                        </button>

                        {/* Context menu */}
                        {menuOpen && menuPosition && (
                          <div
                          ref={menuRef}
                            className="fixed z-[100] w-[190px] rounded-[14px] border border-wa-border bg-wa-surface p-1.5 shadow-[0_14px_40px_rgba(50,65,50,0.16)]"
                            style={{
                              top: menuPosition.top,
                              left: menuPosition.left,
                            }}
                            onClick={(event) =>
                              event.stopPropagation()
                            }
                          >
                            <button
                              type="button"
                              onClick={(event) =>
                                handleAction(
                                  "rename",
                                  chat,
                                  event
                                )
                              }
                              className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-wa-text transition hover:bg-wa-sidebar"
                            >
                              <Pencil
                                size={16}
                                strokeWidth={1.8}
                              />
                              Rename
                            </button>

                            <button
                              type="button"
                              onClick={(event) =>
                                handleAction(
                                  "pin",
                                  chat,
                                  event
                                )
                              }
                              className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-wa-text transition hover:bg-wa-sidebar"
                            >
                              <Pin
                                size={16}
                                strokeWidth={1.8}
                              />
                              {chat.pinned
                                ? "Unpin chat"
                                : "Pin chat"}
                            </button>

                            <button
                              type="button"
                              onClick={(event) =>
                                handleAction(
                                  "archive",
                                  chat,
                                  event
                                )
                              }
                              className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-wa-text transition hover:bg-wa-sidebar"
                            >
                              <Archive
                                size={16}
                                strokeWidth={1.8}
                              />
                              Unarchive
                            </button>

                            <div className="my-1.5 border-t border-wa-border" />

                            <button
                              type="button"
                              onClick={(event) =>
                                handleAction(
                                  "delete",
                                  chat,
                                  event
                                )
                              }
                              className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] text-[#8A5555] transition hover:bg-[#F5EAEA]"
                            >
                              <Trash2
                                size={16}
                                strokeWidth={1.8}
                              />
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        )}
      </div>
    
    

    {/* Bottom */}
<div className="border-t border-wa-border px-5 py-5">
  <div className="space-y-1">

    {/* Sidebar resize handle */}
<div
  role="separator"
  aria-orientation="vertical"
  aria-label="Resize sidebar"
  onMouseDown={startResize}
  className="absolute right-[-3px] top-0 z-50 h-full w-[6px] cursor-col-resize"
>
  <div className="mx-auto h-full w-px opacity-0 transition-opacity hover:opacity-100 bg-wa-accent" />
</div>

    {/* Conversation details */}
    <button
      type="button"
      onClick={() => {
  setOpenMenu(null);
  setMenuPosition(null);
  setEditingChat(null);
  setEditingTitle("");
  onConversationDetails();
}}
      className="flex w-full items-center gap-3 rounded-wa px-3 py-2.5 text-left text-sm text-wa-text transition hover:bg-wa-surface/70"
    >
      <Settings2
        size={16}
        strokeWidth={1.8}
      />

      <span>
        Conversation details
      </span>
    </button>

    {/* About this assistant */}
    <button
      type="button"
      onClick={() => {
  setOpenMenu(null);
  setMenuPosition(null);
  setEditingChat(null);
  setEditingTitle("");
  onAboutAssistant();
}}
      className="flex w-full items-center gap-3 rounded-wa px-3 py-2.5 text-left text-sm text-wa-text transition hover:bg-wa-surface/70"
    >
      <span className="flex h-4 w-4 items-center justify-center text-xs">
        i
      </span>

      <span>
        About this assistant
      </span>
    </button>

  </div>
    </div>   
    </aside>
  );
}