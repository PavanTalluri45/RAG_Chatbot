# Employee Handbook RAG Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot that enables employees to ask natural language questions about an Employee Handbook using semantic search and Google's Gemini AI models.

The application combines a modern AI chat interface with a scalable RAG backend, providing fast, accurate, and context-aware responses.

> **Project Status:** 🚀 Development Complete | 🚧 Deployment Pending

---

# Overview

The Employee Handbook RAG Chatbot allows users to interact with an employee handbook using natural language.

Instead of keyword matching, the system performs semantic search over vector embeddings stored in Chroma Cloud and generates context-aware answers using Google's Gemini models.

The application follows a production-oriented architecture with separate frontend and backend services.

---

# Current Status

## ✅ Backend (Completed)

* Markdown document processing
* Header-aware chunking using LangChain
* Metadata generation
* Gemini Embeddings
* Chroma Cloud vector database
* Semantic retrieval
* Prompt builder
* Gemini LLM integration
* Upstash Redis caching
* FastAPI REST API
* Structured logging
* Error handling
* Retry mechanism
* Performance monitoring
* Production-ready API architecture

---

## ✅ Frontend (Completed)

Built using:

* Next.js (App Router)
* JavaScript
* Tailwind CSS
* shadcn/ui
* Supabase Authentication

Features:

* Modern AI chat interface
* Responsive layout
* Light & Dark theme
* Markdown rendering
* Table rendering
* Chat history
* New Chat
* Soft Delete Chat
* Delete All History
* Authentication
* Protected routes
* Conversation management
* Loading states
* Typing indicator
* Production-ready UI

---

## 🚧 Deployment (Pending)

Deployment is the final remaining step.

Planned deployment:

* **Frontend:** Vercel
* **Backend:** Railway

---

# Tech Stack

## Frontend

* Next.js (App Router)
* JavaScript
* Tailwind CSS
* shadcn/ui
* Supabase Authentication

---

## Backend

* Python
* FastAPI
* LangChain
* Google Gemini API
* Gemini Embedding Model
* Chroma Cloud
* Upstash Redis
* Pydantic

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
Chroma Cloud
            │
            ▼
Semantic Retrieval
            │
            ▼
Prompt Builder
            │
            ▼
Gemini LLM
            │
            ▼
Generated Response
```

---

# Features

* Retrieval-Augmented Generation (RAG)
* Semantic Vector Search
* Gemini Embeddings
* Chroma Cloud Vector Database
* Google Gemini LLM
* Upstash Redis Response Caching
* Markdown Rendering
* Table Rendering
* Conversation History
* Authentication
* Soft Delete Chats
* Responsive AI Chat UI
* Dark & Light Theme
* REST API
* Modular Architecture
* Structured Logging
* Error Handling
* Retry Logic
* Production-ready Design

---

# API Endpoints

| Method | Endpoint  | Description     |
| ------ | --------- | --------------- |
| GET    | `/`       | API Information |
| GET    | `/health` | Health Check    |
| POST   | `/chat`   | Ask a Question  |

---

# Running the Project

Install dependencies

```bash
pip install -r requirements.txt
```

Run the FastAPI server

```bash
python -m uvicorn app.main:app --reload
```

Run the Next.js frontend

```bash
npm install
npm run dev
```

---

# Roadmap

* ✅ Markdown Processing
* ✅ Chunking
* ✅ Embeddings
* ✅ Chroma Cloud Integration
* ✅ Semantic Retrieval
* ✅ Prompt Builder
* ✅ Gemini Integration
* ✅ Upstash Redis Caching
* ✅ FastAPI Backend
* ✅ Next.js Frontend
* ✅ Authentication
* ✅ Chat History
* ✅ Modern AI Chat UI
* ✅ Responsive Design
* ✅ Light & Dark Theme
* ⏳ Backend Deployment (Railway)
* ⏳ Frontend Deployment (Vercel)

---

# Deployment

| Service  | Platform | Status    |
| -------- | -------- | --------- |
| Frontend | Vercel   | ⏳ Pending |
| Backend  | Railway  | ⏳ Pending |

---

# License

This project is intended for educational and portfolio purposes.
