<div align="center">
  <img src="frontend/public/icons.svg" alt="Logo" width="120" />

  # 🧠 AI-Powered Adaptive Diagnostic Engine
  
  **A next-generation intelligent tutoring system that doesn't just tell students if they are wrong—it tells them *why* they are wrong.**

  ![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=flat-square&logo=react)
  ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)
  ![Gemini](https://img.shields.io/badge/AI-Gemini%201.5-8E75B2?style=flat-square)
  ![Eedi](https://img.shields.io/badge/Dataset-Eedi%20Misconceptions-FF6B6B?style=flat-square)
</div>

<br/>

## 📖 Overview

The **Adaptive Diagnostic Engine** is an advanced cognitive tutoring platform built to identify the precise mathematical misconceptions holding students back. Instead of generic "incorrect" feedback, this engine uses a Hybrid AI approach:

1. **Knowledge Graph Integration**: Leverages the official **Eedi dataset** (1,800+ real-world diagnostic math questions) to instantly map common student mistakes to known pedagogical bottlenecks.
2. **Zero-Shot LLM Diagnosis**: For unmapped or unexpected errors, the system seamlessly falls back to **Google Gemini 1.5**, generating highly empathetic, customized pedagogical feedback explaining exactly where the student went wrong in their step-by-step logic.
3. **Cognitive Tracking**: Implements foundational principles of **Neural Cognitive Diagnosis Models (NCDM)** to continuously adapt to the student's mastery level.

## ✨ Key Features

- **🎓 Smart Diagnostic Questions:** Renders complex LaTeX math dynamically, separating equations and text flawlessly.
- **🤖 AI Bottleneck Detection:** Instantly diagnoses over 200 distinct cognitive misconceptions.
- **⚡ Hybrid Architecture:** A blazing-fast React/Vite frontend paired with a robust Python/FastAPI backend.
- **📊 Trace Analysis:** Students can submit step-by-step textual workings which are parsed and evaluated in real-time.

## 🏗️ Architecture

- **Frontend**: `React.js` + `Vite` + `TailwindCSS` + `KaTeX`
- **Backend**: `Python 3` + `FastAPI` + `SQLite` + `SQLAlchemy`
- **AI Core**: `Google Generative AI (Gemini 1.5 Flash)`

## 🚀 Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/Gin-75/adaptive-diagnostic-engine.git
cd adaptive-diagnostic-engine
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

# Add your Gemini API Key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the API
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` in your browser.

## 🌍 Deployment

- **Frontend**: Optimized for deployment on **Cloudflare Pages** or **Vercel**.
- **Backend**: Ready for **Render.com** or **Koyeb** (using `uvicorn`).

## 📄 License
This project was built as an advanced educational research application. The dataset used is sourced from the Eedi Kaggle competition.
