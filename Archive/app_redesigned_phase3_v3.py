import re
import uuid

import streamlit as st

from query_pipeline import get_vector_db, answer_query


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Wellness AI",
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
# CUSTOM UI STYLING — PHASE 3B / V3
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* =====================================================
       DESIGN TOKENS
       ===================================================== */

    :root {
        --wellness-bg: #f6f8f5;
        --wellness-surface: #ffffff;
        --wellness-surface-soft: #f0f4f1;
        --wellness-text: #25332e;
        --wellness-muted: #66736d;
        --wellness-accent: #66877c;
        --wellness-accent-soft: #e7efeb;
        --wellness-border: #dce5e0;
        --wellness-danger-soft: #f8eeee;

        --radius-lg: 16px;
        --radius-md: 12px;
        --radius-sm: 9px;

        --shadow-soft: 0 2px 14px rgba(37, 51, 46, 0.05);
    }

    /* =====================================================
       GLOBAL APP SURFACE
       Streamlit 1.63 uses separate header/bottom surfaces.
       Keep the whole application visually unified.
       ===================================================== */

    .stApp {
        background: var(--wellness-bg) !important;
        color: var(--wellness-text);
    }

    [data-testid="stAppViewContainer"] {
        background: var(--wellness-bg) !important;
    }

    [data-testid="stAppViewBlockContainer"] {
        background: var(--wellness-bg) !important;
    }

    [data-testid="stHeader"] {
        background: var(--wellness-bg) !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Streamlit's pinned bottom area must not become a dark band. */
    [data-testid="stBottom"] {
        background: transparent !important;
        background-color: transparent !important;
        border: 0 !important;
    }

    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }

    .block-container {
        max-width: 860px;
        padding-top: 4.5rem;
        padding-bottom: 7.5rem;
    }

    /* =====================================================
       TYPOGRAPHY
       ===================================================== */

    h1, h2, h3, p, li {
        color: var(--wellness-text);
    }

    h1, h2, h3 {
        letter-spacing: -0.025em;
    }

    p, li {
        line-height: 1.7;
    }

    /* =====================================================
       CALM LANDING SCREEN
       ===================================================== */

    .wellness-landing {
        min-height: 58vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 2rem 1rem 5rem 1rem;
    }

    .wellness-brand {
        color: var(--wellness-accent);
        font-size: 0.88rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1.75rem;
    }

    .wellness-heading {
        color: var(--wellness-text);
        font-size: clamp(2.15rem, 5vw, 3.2rem);
        font-weight: 600;
        line-height: 1.12;
        margin: 0 0 1rem 0;
    }

    .wellness-subheading {
        color: var(--wellness-muted);
        font-size: 1.06rem;
        line-height: 1.7;
        max-width: 530px;
        margin: 0;
    }

    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {
        background: var(--wellness-surface-soft) !important;
        border-right: 1px solid var(--wellness-border);
    }

    section[data-testid="stSidebar"] > div {
        padding: 1.4rem 1rem;
    }

    .sidebar-brand {
        padding: 0.2rem 0.15rem 0.7rem 0.15rem;
    }

    .sidebar-brand-title {
        color: var(--wellness-text);
        font-size: 1.05rem;
        font-weight: 650;
        margin-bottom: 0.35rem;
    }

    .sidebar-brand-subtitle {
        color: var(--wellness-muted);
        font-size: 0.82rem;
        line-height: 1.55;
    }

    section[data-testid="stSidebar"] hr {
        border-color: var(--wellness-border);
        margin: 0.9rem 0;
    }

    section[data-testid="stSidebar"] .stButton > button {
        border-radius: var(--radius-md);
        min-height: 2.45rem;
        box-shadow: none;
    }

    /* Give the primary New Chat control readable contrast. */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: var(--wellness-surface) !important;
        color: var(--wellness-text) !important;
        border: 1px solid var(--wellness-border) !important;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: var(--wellness-accent-soft) !important;
        border-color: var(--wellness-accent) !important;
    }

    /* Chat rows */
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0.25rem;
        margin-bottom: 0.15rem;
    }

    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button {
        min-height: 2.2rem;
        padding: 0.25rem 0.6rem;
        text-align: left;
        border-radius: var(--radius-sm);
    }

    /* =====================================================
       CHAT AREA
       ===================================================== */

    div[data-testid="stChatMessage"] {
        padding-top: 0.75rem;
        padding-bottom: 0.75rem;
    }

    div[data-testid="stChatMessageContent"] {
        max-width: 760px;
    }

    div[data-testid="stChatMessage"] p {
        font-size: 1rem;
        line-height: 1.75;
    }

    /* Subtle user-message surface; assistant remains mostly open. */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        border-radius: var(--radius-lg);
    }

    /* =====================================================
       CHAT INPUT — STREAMLIT 1.63
       ===================================================== */

    [data-testid="stChatInput"] {
        padding-bottom: 1rem !important;
    }

    [data-testid="stChatInput"] > div {
        background: var(--wellness-surface) !important;
        border: 1px solid var(--wellness-border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-soft) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--wellness-text) !important;
        min-height: 3.1rem !important;
        font-size: 1rem !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--wellness-muted) !important;
        opacity: 0.95 !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--wellness-accent) !important;
        box-shadow: 0 0 0 3px rgba(102, 135, 124, 0.10) !important;
    }

    /* Send button */
    [data-testid="stChatInput"] button {
        border-radius: 10px !important;
    }

    /* =====================================================
       EXPANDERS / SECONDARY INFORMATION
       ===================================================== */

    div[data-testid="stExpander"] {
        border: 1px solid var(--wellness-border);
        border-radius: var(--radius-md);
        background: transparent;
        box-shadow: none;
        margin-top: 0.6rem;
    }

    /* =====================================================
       POPOVERS
       ===================================================== */

    div[data-testid="stPopoverBody"] {
        min-width: 190px;
        padding: 0.45rem !important;
        border-radius: var(--radius-md);
    }

    div[data-testid="stPopoverBody"] button {
        min-height: 2.25rem !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.3rem 0.7rem !important;
        margin: 0 !important;
    }

    /* =====================================================
       RESPONSIVE
       ===================================================== */

    @media (max-width: 768px) {
        .block-container {
            max-width: 100%;
            padding: 3.5rem 1rem 7rem 1rem;
        }

        .wellness-landing {
            min-height: 55vh;
            padding-top: 1rem;
        }

        .wellness-heading {
            font-size: 2.15rem;
        }

        .wellness-subheading {
            font-size: 1rem;
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


# The knowledge base is loaded on first query rather than blocking
# the initial calm landing screen. The cached resource remains unchanged.
vector_db = None


def _get_loaded_vector_db():
    try:
        return load_vector_db()
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

    # ── Secondary information ────────────────────────────
    st.divider()

    turn_count = len(_active_conv()) // 2

    with st.expander("Conversation details", expanded=False):
        st.caption(f"Memory: {turn_count} / {MAX_TURNS} turns")

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
# PAGE HEADER
# ---------------------------------------------------------

if not _active_conv():
    st.markdown(
        """
        <main class="wellness-landing" aria-label="Wellness AI welcome">
            <div class="wellness-brand">Wellness AI</div>
            <div class="wellness-heading">Take a moment.</div>
            <div class="wellness-subheading">
                Ask anything about your wellbeing, at your own pace.
            </div>
        </main>
        """,
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
                    _get_loaded_vector_db(),
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
