# Wellness AI — React + Tailwind Frontend

This is the React + Tailwind frontend for the Wellness AI project.

The frontend is connected to the Python FastAPI backend through a thin API layer. Chat requests are sent to the backend /api/chat endpoint, which uses the final Wellness RAG pipeline.

## Architecture

React + Vite
    ↓
src/api.js
    ↓
FastAPI /api/chat
    ↓
Wellness RAG pipeline
    ↓
ChromaDB + embeddings + Granite 4.1 3B

The frontend maintains the conversation UI and client-side chat state, while the backend remains responsible for retrieval, safety routing, evidence grounding, and response generation.

## Current features

- New conversations
- Conversation history in the sidebar
- Chat selection
- Chat renaming
- Pinning chats
- Archiving chats
- Deleting chats
- Persistent chat state during the browser session
- Backend-connected responses
- Retry for failed assistant responses
- Loading states
- Breathing guide
- Responsive chat interface
- Auto-growing chat input

## Backend connection

By default, the frontend connects to:

    http://127.0.0.1:8000

The API base URL can be overridden with:

    VITE_API_BASE_URL

For example:

    VITE_API_BASE_URL=http://127.0.0.1:8000

The frontend sends chat requests to:

    POST /api/chat

with the question and conversation history.

## Run

Install dependencies:

    npm install

Start the development server:

    npm run dev

Vite will print a local URL, normally:

    http://localhost:5173

The Python FastAPI backend must also be running for backend-connected chat responses.

## Production build

To create a production build:

    npm run build

The generated dist/ directory is a build artifact and is intentionally not committed to Git.

## Design goal

**Calm before information.**

The interface intentionally avoids:

- brain/medical imagery
- distress imagery
- alarming colors in the normal interface
- robot avatars
- heavy chat bubbles
- clinical dashboard styling
- unnecessary animation

The frontend is designed to provide a calm conversational interface while leaving safety, retrieval, evidence grounding, and generation responsibilities to the backend.
