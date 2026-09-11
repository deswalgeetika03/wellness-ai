import re
import uuid

import streamlit as st

from query_pipeline import get_vector_db, answer_query


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Wellness RAG Bot",
    page_icon="🌿",
    layout="centered",
)

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

# One "turn" = one user message + one assistant reply.
MAX_TURNS = 15
MAX_ITEMS = MAX_TURNS * 2

# Number of recent turns forwarded to the generation prompt.
CONTEXT_TURNS = 3

# Title generation stop-words.
_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "which",
    "how", "why", "when", "where", "who", "does", "do", "can", "i",
    "my", "me", "you", "your", "it", "to", "for", "of", "in", "on",
    "at", "and", "or", "be", "have", "has", "had", "will", "would",
    "could", "should", "that", "this", "with", "about",
}

# ---------------------------------------------------------
# CUSTOM UI STYLING — PHASE 3B
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* =====================================================
       WELLNESS AI DESIGN TOKENS
       ===================================================== */

    :root {
        --wellness-bg: #f7f7f3;
        --wellness-surface: #ffffff;
        --wellness-text: #26332f;
        --wellness-muted: #69756f;
        --wellness-accent: #6f9186;
        --wellness-accent-soft: #edf3f0;
        --wellness-border: #dfe6e2;
        --wellness-radius: 14px;
        --wellness-radius-small: 10px;
        --wellness-space: 1rem;
    }

    /* =====================================================
       APP SHELL
       ===================================================== */

    .stApp {
        background: var(--wellness-bg);
        color: var(--wellness-text);
    }

    .block-container {
        max-width: 900px;
        padding-top: 2.5rem;
        padding-bottom: 7rem;
    }

    /* Remove the heavy visual feel of default headings */
    h1, h2, h3 {
        color: var(--wellness-text);
        letter-spacing: -0.025em;
    }

    p, li {
        color: var(--wellness-text);
        line-height: 1.65;
    }

    /* =====================================================
       LANDING / PAGE HEADER
       ===================================================== */

    .wellness-landing {
        max-width: 680px;
        margin: 8vh auto 0 auto;
        text-align: center;
        padding: 1rem 1rem 2rem 1rem;
    }

    .wellness-brand {
        color: var(--wellness-muted);
        font-size: 0.92rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-bottom: 2.25rem;
    }

    .wellness-heading {
        color: var(--wellness-text);
        font-size: clamp(2rem, 4vw, 2.75rem);
        font-weight: 600;
        line-height: 1.15;
        margin: 0 0 0.85rem 0;
    }

    .wellness-subheading {
        color: var(--wellness-muted);
        font-size: 1.05rem;
        line-height: 1.65;
        max-width: 540px;
        margin: 0 auto;
    }

    .wellness-chat-intro {
        max-width: 760px;
        margin: 1rem auto 2rem auto;
    }

    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {
        background: #f3f5f2;
    }

    section[data-testid="stSidebar"] > div {
        padding: 1.35rem 1rem;
    }

    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--wellness-text);
    }

    .sidebar-brand {
        padding: 0.35rem 0.2rem 1rem 0.2rem;
    }

    .sidebar-brand-title {
        color: var(--wellness-text);
        font-size: 1.08rem;
        font-weight: 650;
        margin-bottom: 0.3rem;
    }

    .sidebar-brand-subtitle {
        color: var(--wellness-muted);
        font-size: 0.82rem;
        line-height: 1.5;
    }

    section[data-testid="stSidebar"] hr {
        border-color: var(--wellness-border);
        margin: 1rem 0;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] button {
        border-radius: var(--wellness-radius-small);
        min-height: 2.35rem;
        border-color: transparent;
        box-shadow: none;
    }

    section[data-testid="stSidebar"] button:hover {
        border-color: var(--wellness-border);
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        font-weight: 550;
    }

    /* Chat list */
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0.3rem;
        margin-bottom: 0.15rem;
    }

    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button {
        min-height: 2.25rem;
        padding: 0.25rem 0.65rem;
        text-align: left;
    }

    /* =====================================================
       CHAT MESSAGES
       ===================================================== */

    div[data-testid="stChatMessage"] {
        padding-top: 0.75rem;
        padding-bottom: 0.75rem;
    }

    div[data-testid="stChatMessage"] p {
        line-height: 1.7;
        font-size: 1rem;
    }

    div[data-testid="stChatMessageContent"] {
        max-width: 760px;
    }

    /* Keep user message understated */
    div[data-testid="stChatMessage"][data-testid="stChatMessage"] {
        border-radius: var(--wellness-radius);
    }

    /* =====================================================
       PIPELINE INFORMATION
       ===================================================== */

    div[data-testid="stExpander"] {
        margin-top: 0.6rem;
        margin-bottom: 0.35rem;
        border-color: var(--wellness-border);
        border-radius: var(--wellness-radius-small);
    }

    /* =====================================================
       POPOVER MENU
       ===================================================== */

    div[data-testid="stPopoverBody"] {
        padding: 0.45rem !important;
        min-width: 190px;
        border-radius: var(--wellness-radius);
    }

    div[data-testid="stPopoverBody"] button {
        min-height: 2.25rem !important;
        padding: 0.3rem 0.7rem !important;
        margin: 0 !important;
        border-radius: var(--wellness-radius-small) !important;
    }

    div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
        gap: 0.3rem !important;
    }

    /* =====================================================
       CHAT INPUT
       ===================================================== */

    div[data-testid="stChatInput"] {
        padding-bottom: 0.65rem;
    }

    div[data-testid="stChatInput"] textarea {
        border: 1px solid var(--wellness-border);
        border-radius: var(--wellness-radius);
        background: var(--wellness-surface);
        color: var(--wellness-text);
        min-height: 3.25rem;
        box-shadow: 0 2px 12px rgba(38, 51, 47, 0.04);
    }

    div[data-testid="stChatInput"] textarea:focus {
        border-color: var(--wellness-accent);
        box-shadow: 0 0 0 2px rgba(111, 145, 134, 0.12);
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: var(--wellness-muted);
        opacity: 0.9;
    }

    /* =====================================================
       BUTTONS / CONTROLS
       ===================================================== */

    .stButton > button {
        border-radius: var(--wellness-radius-small);
        box-shadow: none;
    }

    /* Regenerate should remain visually secondary */
    div[data-testid="stChatMessage"] .stButton > button {
        min-height: 2.2rem;
        font-size: 0.9rem;
    }

    /* =====================================================
       RESPONSIVE SPACING
       ===================================================== */

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.5rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .wellness-landing {
            margin-top: 5vh;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }

        .wellness-heading {
            font-size: 2rem;
        }

        .wellness-subheading {
            font-size: 0.98rem;
        }
    }

    /* =====================================================
       REDUCED MOTION
       ===================================================== */

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# TITLE GENERATION  (pure Python, no Granite, no new deps)
# ---------------------------------------------------------

def _generate_title(question: str, max_words: int = 4) -> str:
    """
    Derive a short chat title from the first user question by stripping
    stop-words and capitalising the remaining keywords.

    Example:
        "What are common symptoms of anxiety?" -> "Common Symptoms Anxiety"
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", question)
    words = cleaned.split()
    keywords = [w.capitalize() for w in words if w.lower() not in _STOP_WORDS]
    title = " ".join(keywords[:max_words])
    return title if title else question[:40]


# ---------------------------------------------------------
# SESSION-STATE INITIALISATION
# ---------------------------------------------------------

# chats: dict[chat_id -> {"title": str, "conversation": list}]
#
# Each conversation item:
#   user items:      {"role": "user",      "content": str}
#   assistant items: {"role": "assistant", "content": str,
#                     "route": str, "sources": list}

def _new_chat_id() -> str:
    return f"chat_{uuid.uuid4().hex[:8]}"


def _make_empty_chat() -> dict:
    return {"title": "New chat", "conversation": []}


if "chats" not in st.session_state:
    first_id = _new_chat_id()
    st.session_state.chats = {first_id: _make_empty_chat()}
    st.session_state.active_chat_id = first_id

# Stores the chat_id currently pending delete confirmation, or None.
if "delete_confirm_id" not in st.session_state:
    st.session_state.delete_confirm_id = None

# Regenerate flag + the question to re-run.
if "regenerate" not in st.session_state:
    st.session_state.regenerate = False

if "regenerate_question" not in st.session_state:
    st.session_state.regenerate_question = ""

# Stores the chat_id currently in rename mode, or None.
if "rename_active_id" not in st.session_state:
    st.session_state.rename_active_id = None


# ---------------------------------------------------------
# CHAT ACCESSORS
# ---------------------------------------------------------

def _active_chat() -> dict:
    """Return the active chat dict (mutating it mutates session state)."""
    return st.session_state.chats[st.session_state.active_chat_id]


def _active_conv() -> list:
    """Return the active conversation list."""
    return _active_chat()["conversation"]


# ---------------------------------------------------------
# LOAD VECTOR DATABASE  (cached across reruns)
# ---------------------------------------------------------

@st.cache_resource
def load_vector_db():
    return get_vector_db()


try:
    vector_db = load_vector_db()
except Exception as error:
    st.error(
        f"Unable to load the wellness knowledge base.\n\n"
        f"{type(error).__name__}: {error}"
    )
    st.stop()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Wellness AI</div>
            <div class="sidebar-brand-subtitle">
                A calm space to explore wellbeing information.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── New chat button ──────────────────────────────────
    if st.button("✏️ New chat", use_container_width=True):
        new_id = _new_chat_id()
        st.session_state.chats[new_id] = _make_empty_chat()
        st.session_state.active_chat_id = new_id
        st.session_state.delete_confirm_id = None
        st.session_state.regenerate = False
        st.rerun()

    st.divider()

    # ── Chat list ────────────────────────────────────────
    st.caption("**Chats**")

    for chat_id, chat in list(st.session_state.chats.items()):
        # Skip the active chat if it has no messages yet — it is the
        # "pending" new chat that should only appear after the first
        # question is submitted and the title is auto-generated.
        is_active = chat_id == st.session_state.active_chat_id
        if is_active and not chat["conversation"]:
            continue

        label = f"{'▶ ' if is_active else ''}{chat['title']}"

        col_title, col_menu = st.columns([6, 1])

        with col_title:
            if st.button(label, key=f"select_{chat_id}", use_container_width=True):
                if not is_active:
                    st.session_state.active_chat_id = chat_id
                    st.session_state.delete_confirm_id = None
                    st.session_state.regenerate = False
                    st.rerun()

        with col_menu:
            with st.popover("⋯", use_container_width=False):

                # ── Rename ───────────────────────────────
                if st.session_state.rename_active_id != chat_id:
                    if st.button(
                        "✏️ Rename",
                        key=f"rename_btn_{chat_id}",
                        use_container_width=True,
                    ):
                        st.session_state.rename_active_id = chat_id
                        st.rerun()
                else:
                    st.caption("Rename chat")
                    new_name = st.text_input(
                        "New title",
                        value=chat["title"],
                        key=f"rename_input_{chat_id}",
                        label_visibility="collapsed",
                    )
                    if st.button(
                        "Save",
                        key=f"rename_save_{chat_id}",
                        use_container_width=True,
                    ):
                        stripped = new_name.strip()
                        if stripped:
                            st.session_state.chats[chat_id]["title"] = stripped
                        st.session_state.rename_active_id = None
                        st.rerun()
                    if st.button(
                        "Cancel",
                        key=f"rename_cancel_{chat_id}",
                        use_container_width=True,
                    ):
                        st.session_state.rename_active_id = None
                        st.rerun()

                st.divider()

                # ── Delete with inline confirmation ──────
                if st.session_state.delete_confirm_id != chat_id:
                    if st.button("🗑️ Delete", key=f"delete_{chat_id}",
                                 use_container_width=True):
                        st.session_state.delete_confirm_id = chat_id
                        st.rerun()
                else:
                    st.warning("Delete this chat?")
                    if st.button(
                        "Yes, delete",
                        type="primary",
                        key=f"yes_delete_{chat_id}",
                        use_container_width=True,
                    ):
                        del st.session_state.chats[chat_id]
                        # Always keep at least one chat.
                        if not st.session_state.chats:
                            new_id = _new_chat_id()
                            st.session_state.chats[new_id] = _make_empty_chat()
                            st.session_state.active_chat_id = new_id
                        elif chat_id == st.session_state.active_chat_id:
                            st.session_state.active_chat_id = next(
                                iter(st.session_state.chats)
                            )
                        st.session_state.delete_confirm_id = None
                        st.session_state.regenerate = False
                        st.rerun()
                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_{chat_id}",
                        use_container_width=True,
                    ):
                        st.session_state.delete_confirm_id = None
                        st.rerun()

    # ── Conversation details ────────────────────────────
    st.divider()
    turn_count = len(_active_conv()) // 2

    with st.expander("Conversation details", expanded=False):
        st.caption(f"Memory: {turn_count} / {MAX_TURNS} turns")

    # ── About / Responsible AI ──────────────────────────
    with st.expander("About this assistant", expanded=False):
        st.write(
            "This prototype provides educational wellness information "
            "and is not a substitute for professional medical advice."
        )
        st.write(
            "Responses use retrieval-augmented generation with IBM "
            "Granite and a deterministic safety layer."
        )
        st.write(
            "Safety-sensitive requests, including crisis, medication, "
            "and eating-disorder numeric guidance, are intercepted by "
            "the safety layer before retrieval or generation."
        )


# ---------------------------------------------------------
# PAGE HEADER / CALM LANDING STATE
# ---------------------------------------------------------

if not _active_conv():
    st.markdown(
        """
        <div class="wellness-landing">
            <div class="wellness-brand">Wellness AI</div>
            <div class="wellness-heading">Take a moment.</div>
            <div class="wellness-subheading">
                Ask anything about your wellbeing, at your own pace.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="wellness-chat-intro"></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _get_history_for_prompt(conversation: list, n_turns: int) -> list:
    """
    Return the last n_turns of conversation as a plain list of
    {"role": str, "content": str} dicts, suitable for build_prompt().

    Route and sources metadata are intentionally stripped — only the
    text content is relevant for conversational context.
    Returns an empty list when there is no prior conversation.
    """
    if not conversation:
        return []

    recent_items = conversation[-(n_turns * 2):]

    return [
        {"role": item["role"], "content": item["content"]}
        for item in recent_items
    ]


def _append_turn(raw_question: str, result: dict) -> None:
    """
    Append one user+assistant turn to the active chat and evict the
    oldest turn when the 15-turn cap is exceeded.

    Sets the chat title from the first user question if still default.
    raw_question is stored (never the history-augmented form).
    """
    chat = _active_chat()
    conv = chat["conversation"]

    # Auto-title on the very first turn.
    if not conv and chat["title"] == "New chat":
        chat["title"] = _generate_title(raw_question)

    conv.append({
        "role": "user",
        "content": raw_question,
    })
    conv.append({
        "role": "assistant",
        "content": result.get("answer", ""),
        "route": result.get("route", "unknown"),
        "sources": result.get("sources", []),
    })

    # Evict oldest turn (2 items) while over the cap.
    while len(conv) > MAX_ITEMS:
        conv.pop(0)
        conv.pop(0)


def _run_query(raw_question: str) -> None:
    """
    Execute the full answer_query() pipeline for raw_question and
    render the assistant reply bubble.  Used for both normal submissions
    and regenerations so the pipeline is never duplicated.

    route_query() inside answer_query() receives only raw_question.
    history is built from the current active conversation and passed
    only to build_prompt() — the safety layer never sees it.
    """
    conv = _active_conv()
    history = _get_history_for_prompt(conv, CONTEXT_TURNS)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                result = answer_query(
                    vector_db,
                    raw_question,
                    history=history,
                )
            except Exception as error:
                st.error(
                    f"An error occurred while processing your question.\n\n"
                    f"{type(error).__name__}: {error}"
                )
                st.stop()

        answer_text = result.get("answer", "")
        st.write(answer_text)

        route = result.get("route", "unknown")
        sources = result.get("sources", [])

        with st.expander("Pipeline information", expanded=False):
            st.write(f"**Route:** `{route}`")

            if sources:
                st.write("**Sources used:**")
                for source in sources:
                    org = source.get("organization", "Unknown")
                    title = source.get("title", "Unknown")
                    st.write(f"- **{org}** — {title}")
            else:
                st.write(
                    "No retrieval sources were used for this response."
                )

    _append_turn(raw_question, result)


# ---------------------------------------------------------
# RENDER EXISTING CONVERSATION
# ---------------------------------------------------------

conv_snapshot = list(_active_conv())  # snapshot so mutations don't affect render

for idx, item in enumerate(conv_snapshot):

    role = item["role"]

    with st.chat_message(role):

        if role == "assistant":
            st.write(item["content"])

            route = item.get("route", "")
            sources = item.get("sources", [])

            with st.expander("Pipeline information", expanded=False):
                st.write(f"**Route:** `{route}`")

                if sources:
                    st.write("**Sources used:**")
                    for source in sources:
                        org = source.get("organization", "Unknown")
                        title = source.get("title", "Unknown")
                        st.write(f"- **{org}** — {title}")
                else:
                    st.write(
                        "No retrieval sources were used for this response."
                    )

            # Regenerate button shown only on the last assistant message.
            is_last_assistant = (idx == len(conv_snapshot) - 1)
            if is_last_assistant:
                last_user_content = ""
                if idx > 0 and conv_snapshot[idx - 1]["role"] == "user":
                    last_user_content = conv_snapshot[idx - 1]["content"]

                if last_user_content and st.button(
                    "↺ Regenerate", key="regenerate_btn"
                ):
                    # Pop the stale turn from session state (not the
                    # snapshot) and request a regeneration on next rerun.
                    live_conv = _active_conv()
                    if len(live_conv) >= 2:
                        live_conv.pop()  # remove assistant item
                        live_conv.pop()  # remove user item
                    st.session_state.regenerate = True
                    st.session_state.regenerate_question = last_user_content
                    st.rerun()

        else:
            st.write(item["content"])


# ---------------------------------------------------------
# REGENERATE HANDLING  (runs before chat_input on every rerun)
# ---------------------------------------------------------

if st.session_state.regenerate:
    rq = st.session_state.regenerate_question
    st.session_state.regenerate = False
    st.session_state.regenerate_question = ""

    with st.chat_message("user"):
        st.write(rq)

    _run_query(rq)
    st.rerun()


# ---------------------------------------------------------
# CHAT INPUT  (Streamlit pins this to the bottom of the viewport)
# ---------------------------------------------------------

user_input = st.chat_input("What would you like to know?")

if user_input:

    raw_question = user_input.strip()

    if not raw_question:
        st.stop()

    with st.chat_message("user"):
        st.write(raw_question)

    _run_query(raw_question)
