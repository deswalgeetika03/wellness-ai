# Wellness AI

> **A Safety-Aware, Evidence-Grounded AI Assistant for Mental Well-Being**

Wellness AI is a responsible AI prototype designed to make general well-being information more accessible, understandable, and evidence-grounded.

It combines **Retrieval-Augmented Generation (RAG)**, **deterministic safety routing**, **evidence extraction**, **conversational memory**, and **IBM Granite 4.1 3B** in a full-stack web application.

> **Important:** Wellness AI is an informational/supportive prototype. It is not a medical diagnostic system, therapist, or emergency service.

---

## 🌱 SDG Alignment

**Primary SDG: SDG 3 — Good Health and Well-Being**

The project explores how responsible AI can support access to understandable general well-being information while incorporating safety and evidence-grounding mechanisms.

---

## 🎯 Problem

People increasingly use online sources and generative AI for information about stress, emotional well-being, and everyday health concerns. However, general-purpose AI can produce fluent but unsupported responses and may not handle sensitive situations appropriately.

Wellness AI addresses this challenge by combining retrieval, evidence grounding, deterministic safety mechanisms, and language-model generation rather than relying solely on free-form generation.

---

## 💡 Solution

Wellness AI follows a controlled pipeline:

1. A user submits a question.
2. A **deterministic safety layer** checks for sensitive scenarios.
3. Normal queries enter the **RAG pipeline**.
4. Relevant information is retrieved from a curated knowledge base.
5. Retrieved evidence is evaluated and extracted.
6. **IBM Granite 4.1 3B** generates the final response using the relevant context.
7. Conversational memory allows useful context to be maintained across turns.

This architecture separates safety decisions from generative language-model behavior.

---

## 🧠 How It Works

```text
                    User
                     │
                     ▼
              React / Vite UI
                     │
                     ▼
                 FastAPI
                     │
                     ▼
          Deterministic Safety Layer
                │          │
          Sensitive       Normal
             │              │
             ▼              ▼
       Safety Path       RAG Retrieval
                            │
                            ▼
                    ChromaDB + MiniLM
                            │
                            ▼
                    Evidence Extraction
                            │
                            ▼
                  IBM Granite 4.1 3B
                            │
                            ▼
                       Response
```

### Retrieval

- **Vector database:** ChromaDB
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Candidate pool:** 10
- **Final context:** 3 chunks
- **Maximum chunks per source:** 1

The retrieval configuration was evaluated rather than selected only by intuition.

### Generation

- **LLM:** IBM Granite 4.1 3B
- **Temperature:** 0.3
- **Evidence extraction:** enabled before final answer generation

### Safety

The system uses deterministic routing for sensitive categories including:

- Crisis-related situations
- Eating-disorder-related queries
- Medication-related queries
- Diagnostic uncertainty

The safety layer operates before normal generative processing.

---

## ✨ Key Features

- Evidence-grounded conversational responses
- Retrieval-Augmented Generation
- Deterministic safety routing
- Evidence extraction before final generation
- Conversational memory
- New conversations
- Conversation history
- Rename, pin, archive, and delete conversations
- Retry behavior
- Responsive React interface
- Guided breathing exercise
- FastAPI backend
- ChromaDB knowledge retrieval

---

## 🤖 AI Technologies

| Technology | Role |
|---|---|
| **IBM Granite 4.1 3B** | Response generation and evidence extraction |
| **Retrieval-Augmented Generation** | Grounds responses in retrieved information |
| **ChromaDB** | Vector database for knowledge retrieval |
| **Sentence Transformers** | Semantic embeddings |
| **Deterministic Safety Layer** | Routes sensitive scenarios |
| **Conversational Memory** | Maintains useful context across turns |

---

## 🛡️ Responsible AI

Wellness AI was designed with responsible AI considerations as core engineering requirements.

### Safety
Sensitive scenarios are handled through deterministic routing before normal generation.

### Transparency
The RAG pipeline and evidence-extraction stage provide a mechanism for grounding generated responses in retrieved information.

### Fairness
The system is designed to avoid demographic assumptions and discriminatory responses.

### Privacy
The prototype avoids unnecessary collection of personal or sensitive information.

### Limitations
Wellness AI provides general informational/supportive responses. It should not be treated as a replacement for qualified medical, psychological, or emergency support.

---

## 📊 Evaluation

The project was evaluated across retrieval, safety, generation, API, and end-to-end behavior.

### Retrieval

- **Top-1 retrieval:** 67.5%
- **Top-3 retrieval:** 97.5%
- **Candidate pool:** 10
- **Final context:** 3 chunks
- **Maximum chunks per source:** 1

### Safety / Historical Evaluation

- **Route accuracy:** 100%
- **Diagnostic safety:** 95%
- **Grounding:** 75%
- **Tone:** 90%
- **Overall acceptable:** 80%

### Generation

- **18/20 successful final-generation evaluations**
- **90% successful generation evaluation**

The strongest tested intervention was **evidence extraction → answer generation**. A later targeted-claim intervention was evaluated and rejected rather than being retained without evidence.

### System Validation

- **18/18 internal end-to-end checks**
- **6/6 API checks**
- **4/4 safety-isolation checks**
- **Software tests:** 100%

These are internal prototype evaluation results and should not be interpreted as clinical validation or real-world health outcome measurements.

---

## 🖥️ Screenshots

### Main Interface

Add the latest project screenshot here:

```text
docs/screenshots/home.png
```

### AI Conversation

```text
docs/screenshots/conversation.png
```

### Breathing Exercise

```text
docs/screenshots/breathing.png
```

### Responsible Use / About Assistant

```text
docs/screenshots/about.png
```

> Screenshots can be added to this section once the image files are placed in the repository.

---

## 🏗️ Project Structure

```text
PROJECT/
├── Archive/
├── data/
├── Evaluation/
├── Tests/
├── Tools/
├── api.py
├── query_pipeline.py
├── rag_config.py
├── safety_layer.py
├── requirements.txt
├── requirements.freeze.txt
└── wellness_ai_frontend_phase3B/
    └── wellness_ai_frontend/
```

The project keeps evaluation artifacts and archived material separate from the active application code.

---

## ⚙️ Local Setup

### Requirements

- Python 3.14+
- Node.js / npm
- Ollama
- IBM Granite 4.1 3B
- Project dependencies from `requirements.txt`

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Start Ollama

Make sure Ollama is installed and the required model is available:

```powershell
ollama list
```

The project currently uses:

```text
granite4.1:3b
```

### 3. Start the FastAPI backend

From the project root:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

### 4. Start the frontend

```powershell
cd wellness_ai_frontend_phase3B\wellness_ai_frontend
npm install
npm run dev
```

The frontend uses the following environment variable:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For a deployed environment, the API URL can be changed through the frontend environment configuration without changing the core application logic.

---

## 🔗 Demo

**Live Demo:** Coming soon

**Demo Video:** Coming soon

**Project Presentation:** Coming soon

The public deployment is being prepared separately from the validated local implementation.

---

## 🚀 Deployment

Deployment is maintained separately from the frozen project baseline.

The `deployment-free` branch is used for deployment-specific work so that hosting changes do not unintentionally alter the validated RAG, safety, memory, or generation configuration.

A stable public URL will be added here after deployment validation.

---

## 🔬 Development Approach

The project was developed through controlled stages covering:

1. Retrieval quality
2. Safety routing
3. User interface
4. Conversational memory
5. System validation
6. Generation quality
7. Deployment preparation

Major interventions were evaluated before being retained. Changes that did not provide sufficient evidence of improvement were rejected or archived.

This approach helped maintain a controlled and reproducible system rather than continuously modifying the pipeline without measurement.

---

## ⚠️ Limitations

Wellness AI is a prototype and has important limitations:

- It is not clinically validated.
- It does not diagnose medical or psychological conditions.
- It is not a substitute for professional care.
- Internal evaluation does not establish real-world health outcomes.
- The quality of responses depends partly on the underlying knowledge base and retrieved evidence.
- Further user testing and safety evaluation would be required before any broader real-world deployment.

---

## 🔮 Future Scope

Potential future improvements include:

- Broader and more rigorously curated knowledge sources
- Expanded safety evaluation
- Larger-scale user testing
- More comprehensive multilingual support
- Improved observability and deployment monitoring
- Further evaluation of model and retrieval alternatives
- Privacy-preserving analytics for system improvement

Future work should preserve the project's safety and evidence-grounding principles.

---

## 👤 Project

**Wellness AI — A Safety-Aware, Evidence-Grounded AI Assistant for Mental Well-Being**

**Primary SDG:** SDG 3 — Good Health and Well-Being

Built as an AI application exploring responsible use of **RAG, IBM Granite, evidence grounding, deterministic safety mechanisms, and conversational AI**.
