# Employee Handbook AI Assistant

A production-ready AI-powered Employee Handbook Assistant that enables employees to ask natural language questions about company policies using Retrieval-Augmented Generation (RAG), semantic search, and Google's Gemini AI.

The application combines a modern conversational interface with a scalable RAG architecture to deliver fast, accurate, and context-aware responses grounded entirely in the employee handbook.

> **Project Status:** ✅ Production Ready | 🚀 Deployed

---

# Overview

The Employee Handbook AI Assistant transforms a traditional employee handbook into an intelligent conversational assistant.

Instead of keyword searching through lengthy documents, users can ask questions naturally. The system retrieves the most relevant handbook content using semantic vector search and generates grounded responses using Google's Gemini models.

The application follows a modern production architecture with a decoupled frontend and backend.

---

# Live Deployment

### Frontend

Deployed on **Vercel**

### Backend

Deployed on **Vercel (FastAPI)**

---

# Tech Stack

## Frontend

- Next.js (App Router)
- JavaScript
- Tailwind CSS
- shadcn/ui
- Supabase Authentication
- React Markdown

---

## Backend

- Python
- FastAPI
- LangChain
- Google Gemini API
- Gemini Embedding Model
- Chroma Cloud
- Upstash Redis
- Pydantic

---

# AI Pipeline

```text
Employee Handbook (Markdown)
            │
            ▼
Header-aware Chunking
            │
            ▼
Gemini Embeddings
            │
            ▼
Chroma Cloud Vector Database
            │
            ▼
Semantic Retrieval
            │
            ▼
Prompt Builder
            │
            ▼
Google Gemini
            │
            ▼
Grounded AI Response
```

---

# Key Features

- AI-powered Employee Handbook Assistant
- Retrieval-Augmented Generation (RAG)
- Semantic Vector Search
- Gemini Embeddings
- Chroma Cloud Vector Database
- Google Gemini LLM
- FastAPI REST Backend
- Upstash Redis Response Caching
- Markdown Rendering
- Table Rendering
- Responsive Chat Interface
- Conversation History
- Authentication with Supabase
- Soft Delete Conversations
- Dark & Light Theme
- Structured Logging
- Retry Mechanism
- Performance Monitoring
- Production-ready Architecture

---

# API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | API Information |
| GET | `/health` | Health Check |
| POST | `/chat` | Ask Questions |

---

# Running Locally

Install backend dependencies

```bash
pip install -r requirements.txt
```

Run FastAPI

```bash
python -m uvicorn app.main:app --reload
```

Run frontend

```bash
npm install
npm run dev
```

---

# Architecture

```text
Next.js Frontend
        │
        ▼
Next.js API Routes
        │
        ▼
FastAPI Backend
        │
        ▼
Redis Cache
        │
        ▼
Gemini Embeddings
        │
        ▼
Chroma Cloud
        │
        ▼
Gemini LLM
```

---

# Deployment

| Service | Platform |
|----------|----------|
| Frontend | Vercel |
| Backend | Vercel |

---

# License

This project is intended for educational learning and portfolio purposes.
