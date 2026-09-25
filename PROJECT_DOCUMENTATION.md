# 🧠 AI-Powered Adaptive Diagnostic Engine
## Comprehensive Project Documentation

---

### 1. Project Identity
- **Project Name:** AI-Powered Adaptive Diagnostic Engine
- **Primary Domain:** EdTech, Cognitive Diagnosis, AI-Assisted Tutoring
- **Target Audience:** Students, Educators, Schools, and EdTech Platforms.
- **Hackathon Tracks:** AI Tutor, Assessment Revolution

---

### 2. The Problem Statement
Traditional digital assessments suffer from the **"Feedback Gap."** When a student answers a multiple-choice question incorrectly or makes a mistake in a step-by-step math problem, standard platforms only output a binary result: **Correct** or **Incorrect**. 

This creates severe pedagogical issues:
1. **Student Frustration:** Students do not know *why* their logic is flawed, leading to blind guessing and loss of confidence.
2. **Teacher Burnout:** Teachers lack the bandwidth to manually analyze the cognitive missteps of 30+ students simultaneously.
3. **Wasted Data:** The specific nature of a student's error is discarded, preventing adaptive learning systems from targeting the student's actual knowledge gap.

---

### 3. The Solution: Adaptive Diagnostic Engine
Our platform is a next-generation intelligent tutoring system that operates as a **virtual cognitive diagnostician**. It shifts the paradigm from *summative assessment* (grading) to *formative diagnosis* (understanding).

**How it works:**
1. The student is presented with a complex, real-world math problem.
2. The student submits an answer or step-by-step logic.
3. If incorrect, the engine does not just mark it wrong. It cross-references the specific error against a vast pedagogical knowledge graph.
4. For novel or unmapped errors, the engine uses **Generative AI (Gemini 1.5)** to instantly deduce the underlying cognitive misconception (e.g., "Confuses area with perimeter" or "Forgets to distribute the negative sign").
5. The student receives immediate, empathetic, and targeted feedback correcting their specific logical flaw.

---

### 4. Technical Architecture
The project utilizes a modern, hybrid architecture to ensure speed, scalability, and AI flexibility.

#### Frontend (Client-Side)
- **Framework:** React.js + Vite
- **Styling:** TailwindCSS
- **Math Rendering:** `react-katex` (KaTeX) for flawless dynamic rendering of LaTeX equations and mathematical symbols mixed with standard text.
- **Features:** 
  - Dynamic Subject filtering.
  - Interactive Step-by-Step workspace.
  - Persistent Cognitive Feedback Sidebar.

#### Backend (Server-Side)
- **Framework:** FastAPI (Python)
- **Database:** SQLite (SQLAlchemy ORM)
- **Core Logic:** 
  - RESTful API endpoints (`/start_session`, `/submit_process`, `/subjects`).
  - Session state tracking and cognitive mastery updating.

#### AI & Data Core
- **Generative AI:** Google Gemini 1.5 Flash (via `google-generativeai` SDK) is used for **Zero-Shot Cognitive Diagnosis**.
- **Dataset:** The engine is seeded with the **Eedi Misconceptions Dataset** (from Kaggle), containing over 1,860+ high-quality math questions, complete with known distractors and official pedagogical misconceptions.

---

### 5. The Role of Generative AI (Gemini)
Traditional EdTech relies on hardcoded decision trees. If a student makes an error that the programmer didn't predict, the system crashes or outputs a generic "Unknown Error."

**Our innovation is a Hybrid Diagnostic Pipeline:**
1. **Fast-Path (Hardcoded):** If the student selects a distractor pre-mapped by Eedi's expert teachers, the system instantly returns the exact misconception from the database.
2. **AI Fallback (Gemini):** If the student's error is novel, or if the database lacks a mapped misconception for a specific distractor, the system triggers Gemini 1.5. 
   - **Prompt Engineering:** We pass the Construct Name, Subject, Question Text, Correct Answer, and the Student's Flawed Trace to Gemini.
   - **Output:** Gemini acts as an expert pedagogue, generating a 3-10 word official-sounding bottleneck, and a 2-sentence empathetic explanation.

This ensures **100% diagnostic coverage** across all possible student errors.

---

### 6. Database Schema
The engine utilizes a relational database to track questions and student cognitive mastery.

- **`questions` Table:**
  - `id`: Integer
  - `content`: Text (Mixed Markdown & LaTeX)
  - `subject`: String (e.g., "Geometry", "Algebra")
  - `structural_family`: String (Specific mathematical construct)
  - `options`: JSON (Array of distractors, booleans, and diagnoses)
  - `solution`: Text

- **`attempts` Table (NCDM Tracking):**
  - Tracks every student interaction, preserving the `error_signature` to feed into future Neural Cognitive Diagnosis Models (NCDM) for adaptive difficulty scaling.

---

### 7. Setup and Deployment
- **Repository:** https://github.com/Gin-75/adaptive-diagnostic-engine
- **Frontend Hosting:** Designed for **Cloudflare Pages** or Vercel.
- **Backend Hosting:** Designed for **Render.com** (with Python/FastAPI environment).

---

### 8. Future Roadmap
1. **Full NCDM Integration:** Utilize the stored error signatures to train a neural network that predicts a student's likelihood of answering future questions correctly, dynamically adjusting the difficulty of the next question served.
2. **Teacher Dashboard:** A real-time analytics panel for educators to see a heat-map of cognitive bottlenecks across their entire classroom.
3. **Multi-Modal Input:** Allowing students to upload pictures of their handwritten math work, using Gemini Vision to parse the handwriting and diagnose the error.
