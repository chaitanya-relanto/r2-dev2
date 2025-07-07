# R2-Dev2: AI Developer Productivity Assistant

Welcome to R2-Dev2, a full-stack AI-powered assistant engineered to streamline your development workflow. By integrating a sophisticated FastAPI backend with a responsive Next.js frontend, R2-Dev2 offers a powerful conversational interface to tackle a wide array of development tasks, from querying databases with natural language to summarizing pull requests on the fly.

## Table of Contents

- [Features](#features)
- [Architecture & Core Components](#architecture--core-components)
  - [Backend Architecture](#backend-architecture)
  - [Frontend Architecture](#frontend-architecture)
- [Tech Stack](#tech-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
  - [Running Locally](#running-locally)
  - [Deployment with Docker Compose](#deployment-with-docker-compose)

## Features

**Backend:**
- **Conversational AI Agent:** Built with LangGraph to understand complex queries and route them to the correct tool.
- **Natural Language to SQL (NL2SQL):** Query your database using plain English.
- **Retrieval-Augmented Generation (RAG):** Utilizes PGVector to provide context-aware answers from technical documents and learning resources.
- **LLM Observability:** Integrated with LangSmith for tracing and debugging.
- **Tool Integration:** Connects to services like Jira and Git to fetch tickets, summarize pull requests, and more.

**Frontend:**
- **Interactive Chat Interface:** A responsive and intuitive chat UI for interacting with the AI agent, with support for Markdown rendering.
- **Developer Dashboard:** A centralized view of your work, including ticket statuses, recent pull requests, and quick actions.
- **Session Management:** Easily switch between past conversations or start new ones.
- **Secure Authentication:** A robust login system to protect user data.

## Architecture & Core Components

### Backend Architecture

The backend is built around a powerful **LangGraph** agent that serves as the brain of the application. It determines user intent and routes queries to the appropriate tools, such as the NL2SQL engine or the RAG pipeline.

![Chat Agent Graph](./backend/artifacts/chat_graph.png)

-   **RAG with PGVector:** We use OpenAI's `text-embedding-3-small` model to generate vector embeddings for documents and learning materials. These are stored in PostgreSQL with the PGVector extension for fast and accurate semantic search.
-   **NL2SQL:** This component translates natural language questions into SQL queries, allowing users to conversationally access structured data.
-   **LangSmith:** All LLM-related operations are traced with LangSmith for observability and debugging.

### Frontend Architecture

The frontend is a modern server-side rendered application built with Next.js and TypeScript.

-   **Dashboard:** Provides a developer-centric overview of ongoing work, including Jira tickets and pull requests.
-   **Chat Interface:** A carefully designed conversational UI that supports streaming responses, Markdown rendering, and recommended follow-up actions.
-   **State Management:** Zustand is used for lightweight and efficient global state management.

## Tech Stack

### Backend
- Python 3.13
- FastAPI
- LangChain & LangGraph
- PostgreSQL with PGVector
- Pipenv
- Docker
- LangSmith (for LLM Observability)

### Frontend
- Next.js (React)
- TypeScript
- Material-UI & Tailwind CSS
- Zustand for state management
- Lucide React for icons

## Project Structure

This is a monorepo containing the `backend` and `frontend` applications.

```
r2-dev2/
├── backend/            # FastAPI backend service
├── frontend/           # Next.js frontend application
├── docker-compose.yml  # Docker Compose for deployment
└── README.md           # This file
```

## Getting Started

### Prerequisites
- Python 3.13 & Pipenv
- Node.js (v20+) & npm
- Docker & Docker Compose

### Installation

First, you'll need to clone the repository to your local machine.
```bash
git clone <repository-url>
cd r2-dev2
```

Once cloned, you can proceed with installing the dependencies for each service:

1.  **Backend Dependencies:**
    ```bash
    cd backend
    pipenv install
    cd ..
    ```
2.  **Frontend Dependencies:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

### Environment Configuration

Both applications require environment variables to be set.

-   **Backend:** Create a `.env` file inside `backend/configs/secrets/`. You can use `backend/configs/secrets/.env.example` as a a reference.
-   **Frontend:** Create a `.env.local` file inside the `frontend/` directory. It should contain `NEXT_PUBLIC_API_URL=http://localhost:8000`.

Refer to the README file in each respective directory for detailed environment variable configurations.

## Running the Application

### Running Locally

**Backend:**
To run the backend service, which will be available at `http://localhost:8000`:
```bash
cd backend
pipenv shell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
To run the frontend application, which will be available at `http://localhost:3000`:
```bash
cd frontend
npm run dev
```

### Deployment with Docker Compose

The simplest way to run both the frontend and backend is with Docker Compose. This repository includes a `docker-compose.yml` file that orchestrates both services.

The Compose file defines two services:
-   `backend`: Builds the image from the `backend` directory and runs it, exposing port `8015` on the host. It uses the `.env` files in `backend/configs/` for configuration.
-   `frontend`: Builds the image from the `frontend` directory and runs it on port `3000`. It depends on the backend and uses the `.env.local` file for configuration.

Before running, ensure your `.env` files are correctly configured. To build and run the entire application stack, run the following command from the root directory:

```bash
docker-compose up --build
```

- The frontend will be accessible at `http://localhost:3000`.
- The backend API will be accessible at `http://localhost:8015`.
